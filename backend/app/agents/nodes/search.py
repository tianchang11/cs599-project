import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.search_service import SearchService, SearchResult

logger = logging.getLogger(__name__)


@register_node("search")
class SearchNode(BaseNode):
    name = "search"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        search_svc = SearchService()
        all_sources: list[dict] = []
        results: dict[str, list[SearchResult]] = {}
        search_depth = state.get("search_depth", 8)

        for i, sq in enumerate(state["sub_queries"]):
            logger.info(f"[Search] Sub-query {i+1}/{len(state['sub_queries'])}: {sq}")
            hits = search_svc.search(sq, max_results=search_depth)
            results[sq] = hits
            for h in hits:
                if {"url": h["url"], "title": h["title"]} not in all_sources:
                    all_sources.append({"url": h["url"], "title": h["title"]})
            self.emit(state, "searching", f"已完成 {i+1}/{len(state['sub_queries'])} 个子查询的检索", 20 + (i * 15))

        return self.emit(
            {**state, "search_results": results, "sources": all_sources},
            "searching",
            f"检索完成，共获取 {len(all_sources)} 个来源",
            40,
        )
