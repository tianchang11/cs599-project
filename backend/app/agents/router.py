import logging
from typing import Any

from app.agents.classifier import classify_query, QueryCategory
from app.agents.strategies.base import ResearchStrategy, get_strategy, STRATEGIES

logger = logging.getLogger(__name__)


class StrategyRouter:
    def __init__(self):
        self._overrides: dict[str, str] = {}

    def set_override(self, user_id: str, strategy_name: str) -> None:
        self._overrides[user_id] = strategy_name
        logger.info(f"[StrategyRouter] Override set for user {user_id}: {strategy_name}")

    def clear_override(self, user_id: str) -> None:
        self._overrides.pop(user_id, None)

    async def route(
        self,
        query: str,
        api_key: str,
        provider: str,
        model: str,
        user_id: str | None = None,
        explicit_strategy: str | None = None,
    ) -> tuple[ResearchStrategy, QueryCategory, float]:
        if explicit_strategy and explicit_strategy in STRATEGIES:
            strategy = get_strategy(explicit_strategy)
            logger.info(f"[StrategyRouter] Using explicit strategy: {explicit_strategy}")
            category = explicit_strategy
            confidence = 1.0
            return strategy, category, confidence

        if user_id and user_id in self._overrides:
            strategy_name = self._overrides[user_id]
            strategy = get_strategy(strategy_name)
            logger.info(f"[StrategyRouter] Using override strategy for user {user_id}: {strategy_name}")
            return strategy, strategy_name, 1.0

        category, confidence = await classify_query(query, api_key, provider, model)
        strategy = get_strategy(category)

        logger.info(
            f"[StrategyRouter] Routed query to '{category}' strategy "
            f"(confidence: {confidence:.2f}, max_iterations: {strategy.max_iterations})"
        )

        return strategy, category, confidence


strategy_router = StrategyRouter()
