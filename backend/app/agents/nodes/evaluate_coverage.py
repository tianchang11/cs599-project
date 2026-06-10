import json
import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.evaluation import EVALUATE_COVERAGE_SYSTEM, EVALUATE_COVERAGE_USER

logger = logging.getLogger(__name__)


@register_node("evaluate_coverage")
class EvaluateCoverageNode(BaseNode):
    name = "evaluate_coverage"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        sub_content = "\n\n".join([
            f"=== 子查询: {sq} ===\n{content[:500]}"
            for sq, content in state.get("filtered_content", {}).items()
        ])

        text = await chat_completion(
            messages=[
                {"role": "system", "content": EVALUATE_COVERAGE_SYSTEM},
                {"role": "user", "content": EVALUATE_COVERAGE_USER.format(
                    query=state["query"],
                    sub_queries=state.get("sub_queries", []),
                    synthesis_summary=state.get("synthesis_text", "")[:2000],
                )},
            ],
            api_key=state["api_key"],
            provider=state["provider"],
            model=state["model"],
            temperature=0.3,
        )

        try:
            result = json.loads(text)
            coverage_score = float(result.get("score", 0.5))
            needs_more_research = result.get("needs_more_research", False)
            missing_aspects = result.get("missing_aspects", [])
        except (json.JSONDecodeError, ValueError):
            coverage_score = 0.5
            needs_more_research = False
            missing_aspects = []

        coverage_threshold = state.get("coverage_threshold", 6.0)
        if coverage_score < coverage_threshold and not needs_more_research:
            needs_more_research = True
            missing_aspects.append(f"覆盖度评分({coverage_score:.1f})低于阈值({coverage_threshold})，需要补充研究")

        logger.info(f"[EvaluateCoverage] Score: {coverage_score}, Needs more: {needs_more_research}")

        new_state = {
            **state,
            "coverage_score": coverage_score,
            "needs_more_research": needs_more_research,
            "missing_aspects": missing_aspects,
        }

        if needs_more_research and state.get("iteration", 0) < 3:
            return self.emit(
                new_state,
                "evaluating",
                f"覆盖度评分: {coverage_score:.1f}/10，存在未覆盖的方面，需要补充研究",
                72,
            )
        else:
            return self.emit(
                new_state,
                "evaluating",
                f"覆盖度评分: {coverage_score:.1f}/10，覆盖充分，开始撰写报告",
                72,
            )
