import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.planning import PLANNING_SYSTEM, PLANNING_USER

logger = logging.getLogger(__name__)


@register_node("planning")
class PlanningNode(BaseNode):
    name = "planning"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        max_sub_queries = state.get("max_sub_queries", 5)
        logger.info(f"[Planning] Query: {state['query']}, max_sub_queries: {max_sub_queries}")

        context = state.get("pdf_context", "")
        user_prompt = PLANNING_USER.format(query=state["query"], context=context)

        text = await chat_completion(
            messages=[
                {"role": "system", "content": PLANNING_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            api_key=state["api_key"],
            provider=state["provider"],
            model=state["model"],
            temperature=0.5,
        )

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        sub_queries = [l.lstrip("0123456789.、) ").strip() for l in lines if l and l[0].isdigit()]
        if not sub_queries:
            sub_queries = [l.strip() for l in lines if len(l) > 20]

        trimmed = sub_queries[:max_sub_queries]
        logger.info(f"[Planning] Generated {len(trimmed)} sub-queries (max: {max_sub_queries}): {trimmed}")
        return self.emit(
            {**state, "sub_queries": trimmed},
            "planning",
            f"已将问题拆解为 {len(trimmed)} 个子查询",
            10,
        )
