import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.planning import REFINE_QUERIES_SYSTEM, REFINE_QUERIES_USER

logger = logging.getLogger(__name__)


@register_node("refine_queries")
class RefineQueriesNode(BaseNode):
    name = "refine_queries"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        suggestions = state.get("refinement_suggestions", [])
        existing_queries = state.get("sub_queries", [])

        text = await chat_completion(
            messages=[
                {"role": "system", "content": REFINE_QUERIES_SYSTEM},
                {"role": "user", "content": REFINE_QUERIES_USER.format(
                    query=state["query"],
                    existing_queries=existing_queries,
                    suggestions=suggestions,
                )},
            ],
            api_key=state["api_key"],
            provider=state["provider"],
            model=state["model"],
            temperature=0.5,
        )

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        new_queries = [l.lstrip("0123456789.、) ").strip() for l in lines if l and l[0].isdigit()]
        if not new_queries:
            new_queries = [l.strip() for l in lines if len(l) > 20]

        existing_urls = {s["url"] for s in state.get("sources", [])}

        merged_queries = list(existing_queries)
        for q in new_queries[:3]:
            if q not in merged_queries:
                merged_queries.append(q)

        logger.info(f"[RefineQueries] Refined to {len(merged_queries)} queries: {merged_queries}")
        return self.emit(
            {**state, "sub_queries": merged_queries[:7]},
            "refining",
            f"优化搜索策略，当前 {len(merged_queries[:7])} 个子查询",
            15,
        )
