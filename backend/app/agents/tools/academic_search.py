import logging
import httpx
from typing import Any

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("academic_search")
class AcademicSearchTool(BaseTool):
    name = "academic_search"
    description = "Search for academic papers and scholarly articles. Returns titles, authors, abstracts, and links to papers."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The academic search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        if not query:
            return ToolResult(success=False, error="Query is required")

        try:
            results = await self._search_semantic_scholar(query, max_results)
            if results:
                return ToolResult(success=True, data=results)

            results = await self._search_arxiv(query, max_results)
            return ToolResult(success=True, data=results)
        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            return ToolResult(success=False, error=str(e))

    async def _search_semantic_scholar(self, query: str, max_results: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={
                        "query": query,
                        "limit": max_results,
                        "fields": "title,authors,abstract,url,year,citationCount",
                    },
                )
                if resp.status_code != 200:
                    return []

                data = resp.json()
                papers = []
                for p in data.get("data", []):
                    authors = ", ".join(a.get("name", "") for a in (p.get("authors") or [])[:3])
                    papers.append({
                        "title": p.get("title", ""),
                        "authors": authors,
                        "abstract": (p.get("abstract") or "")[:500],
                        "url": p.get("url", ""),
                        "year": p.get("year"),
                        "citations": p.get("citationCount", 0),
                    })
                return papers
        except Exception:
            return []

    async def _search_arxiv(self, query: str, max_results: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "http://export.arxiv.org/api/query",
                    params={
                        "search_query": f"all:{query}",
                        "max_results": max_results,
                        "sortBy": "relevance",
                    },
                )
                if resp.status_code != 200:
                    return []

                import re
                entries = re.findall(r'<entry>(.*?)</entry>', resp.text, re.DOTALL)
                papers = []
                for entry in entries:
                    title = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                    summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                    link = re.search(r'<id>(.*?)</id>', entry)
                    authors = re.findall(r'<name>(.*?)</name>', entry)

                    papers.append({
                        "title": title.group(1).strip() if title else "",
                        "authors": ", ".join(authors[:3]),
                        "abstract": summary.group(1).strip()[:500] if summary else "",
                        "url": link.group(1).strip() if link else "",
                        "year": None,
                        "citations": None,
                    })
                return papers
        except Exception:
            return []
