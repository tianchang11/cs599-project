from typing import TypedDict, Literal
import logging

try:
    from tavily import TavilyClient
    HAS_TAVILY = True
except ImportError:
    HAS_TAVILY = False

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


class SearchResult(TypedDict):
    url: str
    title: str
    content: str
    score: float


class SearchService:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.tavily_api_key

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        if not HAS_TAVILY:
            logger.warning("Tavily not installed, returning mock results")
            return [
                SearchResult(
                    url=f"https://example.com/{i}",
                    title=f"Result for '{query}' - Page {i}",
                    content=f"This is a mock search result for the query '{query}'. "
                            f"In production, this would contain real web content.",
                    score=1.0 - (i * 0.05),
                )
                for i in range(max_results)
            ]

        try:
            client = TavilyClient(api_key=self._api_key)
            results = client.search(query=query, max_results=max_results)
            return [
                SearchResult(
                    url=r["url"],
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 1.0),
                )
                for r in results.get("results", [])
            ]
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise ServiceUnavailableError(f"Search service unavailable: {e}")


search_service = SearchService()
