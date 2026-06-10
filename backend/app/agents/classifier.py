import json
import logging
import re
from typing import Literal
from functools import lru_cache

from app.services.llm_service import chat_completion

logger = logging.getLogger(__name__)

QueryCategory = Literal["factual", "analytical", "exploratory", "comparative"]

CLASSIFICATION_SYSTEM = """You are a query classifier for a deep research system. Classify the given research query into one of these categories:

1. "factual" - Simple factual questions that need a direct answer (e.g., "What is the GDP of Japan?", "When was the iPhone first released?")
2. "analytical" - Complex questions requiring deep analysis and synthesis from multiple sources (e.g., "What are the long-term economic impacts of AI automation?", "How does climate change affect global food security?")
3. "exploratory" - Open-ended exploratory questions seeking broad understanding (e.g., "Tell me about the current state of quantum computing", "Overview of renewable energy technologies")
4. "comparative" - Questions comparing two or more things (e.g., "Compare React vs Vue vs Angular for enterprise applications", "Differences between machine learning and deep learning")

Consider these signals:
- Factual: short queries, "what is/when/who/where", single-answer expected
- Analytical: "how/why/impact/implications", requires multi-source synthesis, longer queries
- Exploratory: "overview/state of/tell me about/current landscape", broad scope
- Comparative: "vs/difference/compare/better than/versus", multiple entities to compare

Output ONLY a JSON object with:
- "category": one of "factual", "analytical", "exploratory", "comparative"
- "confidence": float from 0.0 to 1.0
- "reasoning": brief explanation of the classification
- "suggested_sub_queries_count": integer (3 for factual, 5 for analytical, 7 for exploratory, 6 for comparative)

Output ONLY valid JSON, no other text."""

CLASSIFICATION_USER = """Research query: {query}

Classify this query."""

_COMPARATIVE_PATTERNS = re.compile(
    r'\b(vs\.?|versus|compare|comparison|differ|better|worse|versus|against|or\s+)\b',
    re.IGNORECASE,
)
_ANALYTICAL_PATTERNS = re.compile(
    r'\b(impact|implication|effect|consequence|why|how|cause|result|analysis|analyze|evaluate|assess)\w*\b',
    re.IGNORECASE,
)
_EXPLORATORY_PATTERNS = re.compile(
    r'\b(overview|state of|landscape|current|trend|tell me about|introduction|guide|survey|review)\w*\b',
    re.IGNORECASE,
)
_FACTUAL_PATTERNS = re.compile(
    r'\b(what is|who is|when (was|did|is)|where is|how (many|much|old)|define|definition)\w*\b',
    re.IGNORECASE,
)


def _keyword_precheck(query: str) -> tuple[QueryCategory | None, float]:
    scores: dict[QueryCategory, int] = {"factual": 0, "analytical": 0, "exploratory": 0, "comparative": 0}

    if _COMPARATIVE_PATTERNS.search(query):
        scores["comparative"] += 2
    if _ANALYTICAL_PATTERNS.search(query):
        scores["analytical"] += 2
    if _EXPLORATORY_PATTERNS.search(query):
        scores["exploratory"] += 2
    if _FACTUAL_PATTERNS.search(query):
        scores["factual"] += 2

    words = query.split()
    if len(words) <= 5:
        scores["factual"] += 1
    elif len(words) >= 15:
        scores["analytical"] += 1

    if " and " in query.lower() or " or " in query.lower():
        scores["comparative"] += 1

    max_score = max(scores.values())
    if max_score == 0:
        return None, 0.0

    best = max(scores, key=lambda k: scores[k])
    confidence = min(max_score / 4.0, 1.0)
    return best, confidence


_classification_cache: dict[str, tuple[QueryCategory, float]] = {}


async def classify_query(
    query: str,
    api_key: str,
    provider: str,
    model: str,
    use_cache: bool = True,
) -> tuple[QueryCategory, float]:
    if use_cache and query in _classification_cache:
        cached = _classification_cache[query]
        logger.info(f"[QueryClassifier] Cache hit for: {query[:50]}")
        return cached

    keyword_category, keyword_confidence = _keyword_precheck(query)
    if keyword_confidence >= 0.75:
        logger.info(f"[QueryClassifier] Keyword precheck: {keyword_category} (confidence: {keyword_confidence:.2f})")
        result = (keyword_category, keyword_confidence)
        _classification_cache[query] = result
        return result

    try:
        text = await chat_completion(
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM},
                {"role": "user", "content": CLASSIFICATION_USER.format(query=query)},
            ],
            api_key=api_key,
            provider=provider,
            model=model,
            temperature=0.1,
        )

        parsed = json.loads(text)
        category = parsed.get("category", "analytical")
        confidence = float(parsed.get("confidence", 0.5))

        valid_categories = ("factual", "analytical", "exploratory", "comparative")
        if category not in valid_categories:
            logger.warning(f"Invalid category '{category}', defaulting to 'analytical'")
            category = "analytical"

        if keyword_category and confidence < 0.6:
            logger.info(f"[QueryClassifier] LLM confidence low ({confidence:.2f}), using keyword result: {keyword_category}")
            category = keyword_category
            confidence = max(confidence, keyword_confidence)

        logger.info(f"[QueryClassifier] Query classified as '{category}' (confidence: {confidence:.2f})")
        result = (category, confidence)
        _classification_cache[query] = result
        return result

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Query classification failed: {e}, defaulting to 'analytical'")
        if keyword_category:
            return (keyword_category, keyword_confidence)
        return "analytical", 0.5


def clear_classification_cache():
    _classification_cache.clear()
