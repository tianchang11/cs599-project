import pytest
from app.agents.classifier import _keyword_precheck, classify_query, clear_classification_cache
from app.agents.router import StrategyRouter
from app.agents.strategies.base import get_strategy


class TestKeywordPrecheck:
    def test_factual_pattern(self):
        category, confidence = _keyword_precheck("What is the GDP of Japan?")
        assert category == "factual"
        assert confidence > 0

    def test_analytical_pattern(self):
        category, confidence = _keyword_precheck("What are the impacts of AI on employment?")
        assert category == "analytical"
        assert confidence > 0

    def test_exploratory_pattern(self):
        category, confidence = _keyword_precheck("Overview of quantum computing landscape")
        assert category == "exploratory"
        assert confidence > 0

    def test_comparative_pattern(self):
        category, confidence = _keyword_precheck("React vs Vue comparison")
        assert category == "comparative"
        assert confidence > 0

    def test_no_pattern_returns_none(self):
        category, confidence = _keyword_precheck("xyz abc def ghi jkl mno")
        assert category is None
        assert confidence == 0.0

    def test_short_query_favors_factual(self):
        category, confidence = _keyword_precheck("GDP Japan")
        assert category == "factual"

    def test_long_query_favors_analytical(self):
        long_query = "How does the implementation of carbon pricing mechanisms affect industrial competitiveness and environmental outcomes in developing economies"
        category, confidence = _keyword_precheck(long_query)
        assert category == "analytical"


class TestStrategyRouter:
    @pytest.mark.asyncio
    async def test_explicit_strategy(self):
        router = StrategyRouter()
        strategy, category, confidence = await router.route(
            query="test",
            api_key="",
            provider="openai",
            model="gpt-4o",
            explicit_strategy="factual",
        )
        assert strategy.name == "factual"
        assert confidence == 1.0

    @pytest.mark.asyncio
    async def test_user_override(self):
        router = StrategyRouter()
        router.set_override("user_123", "exploratory")
        strategy, category, confidence = await router.route(
            query="test",
            api_key="",
            provider="openai",
            model="gpt-4o",
            user_id="user_123",
        )
        assert strategy.name == "exploratory"
        assert confidence == 1.0

    def test_clear_override(self):
        router = StrategyRouter()
        router.set_override("user_123", "exploratory")
        router.clear_override("user_123")
        assert "user_123" not in router._overrides
