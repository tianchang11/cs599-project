import json
import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.agents.tools.executor import ToolExecutor
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)


@register_node("tool_search")
class ToolSearchNode(BaseNode):
    name = "tool_search"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        sub_queries = state.get("sub_queries", [])
        search_depth = state.get("search_depth", 8)
        all_sources: list[dict] = []
        results: dict[str, list] = {}

        executor = ToolExecutor(tool_names=["web_search", "academic_search"])

        for i, sq in enumerate(sub_queries):
            logger.info(f"[ToolSearch] Sub-query {i+1}/{len(sub_queries)}: {sq}")

            try:
                tool_result = await executor.run_with_tools(
                    prompt=f"Search for information about: {sq}\nUse web_search and/or academic_search to find relevant results.",
                    api_key=state["api_key"],
                    provider=state["provider"],
                    model=state["model"],
                    max_rounds=2,
                )

                search_data = []
                for tr in tool_result.get("tool_results", []):
                    if tr["success"] and tr["data"]:
                        if isinstance(tr["data"], list):
                            for item in tr["data"]:
                                entry = {
                                    "url": item.get("url", ""),
                                    "title": item.get("title", ""),
                                    "content": item.get("content", item.get("abstract", "")),
                                    "score": item.get("score", 0.5),
                                }
                                search_data.append(entry)
                                if {"url": entry["url"], "title": entry["title"]} not in all_sources:
                                    all_sources.append({"url": entry["url"], "title": entry["title"]})

                if not search_data:
                    search_svc = SearchService()
                    hits = search_svc.search(sq, max_results=search_depth)
                    results[sq] = hits
                    for h in hits:
                        if {"url": h["url"], "title": h["title"]} not in all_sources:
                            all_sources.append({"url": h["url"], "title": h["title"]})
                else:
                    results[sq] = search_data

            except Exception as e:
                logger.warning(f"[ToolSearch] Tool-based search failed for '{sq}': {e}, falling back to direct search")
                search_svc = SearchService()
                hits = search_svc.search(sq, max_results=search_depth)
                results[sq] = hits
                for h in hits:
                    if {"url": h["url"], "title": h["title"]} not in all_sources:
                        all_sources.append({"url": h["url"], "title": h["title"]})

            self.emit(state, "searching", f"已完成 {i+1}/{len(sub_queries)} 个子查询的检索", 20 + (i * 15))

        return self.emit(
            {**state, "search_results": results, "sources": all_sources},
            "searching",
            f"检索完成，共获取 {len(all_sources)} 个来源",
            40,
        )
