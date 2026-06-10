import logging
from typing import Any

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.tools.registry import register_tool
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)


@register_tool("web_search")
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information on a given query. Returns a list of relevant results with titles, URLs, and content snippets."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 8,
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 8)

        if not query:
            return ToolResult(success=False, error="Query is required")

        try:
            search_svc = SearchService()
            results = search_svc.search(query, max_results=max_results)
            return ToolResult(
                success=True,
                data=[
                    {
                        "url": r["url"],
                        "title": r["title"],
                        "content": r["content"],
                        "score": r["score"],
                    }
                    for r in results
                ],
            )
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(success=False, error=str(e))
