import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.filter import FILTER_SYSTEM, FILTER_USER

logger = logging.getLogger(__name__)


@register_node("filter")
class FilterNode(BaseNode):
    name = "filter"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        filtered: dict[str, str] = {}
        total = len(state["sub_queries"])

        for i, (sq, hits) in enumerate(state["search_results"].items()):
            formatted_results = "\n\n".join([
                f"[{j+1}] {h['title']}\nURL: {h['url']}\nContent: {h['content'][:500]}"
                for j, h in enumerate(hits)
            ])

            content = await chat_completion(
                messages=[
                    {"role": "system", "content": FILTER_SYSTEM},
                    {"role": "user", "content": FILTER_USER.format(sub_query=sq, search_results=formatted_results)},
                ],
                api_key=state["api_key"],
                provider=state["provider"],
                model=state["model"],
                temperature=0.3,
            )

            filtered[sq] = content
            logger.info(f"[Filter] Processed sub-query {i+1}/{total}")
            self.emit(state, "filtering", f"已完成 {i+1}/{total} 个结果的内容分析与筛选", 45 + (i * 8))

        return self.emit(
            {**state, "filtered_content": filtered},
            "filtering",
            "内容筛选完成，正在进行综合分析",
            60,
        )
