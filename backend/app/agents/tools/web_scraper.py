import logging
import httpx
from typing import Any

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("web_scraper")
class WebScraperTool(BaseTool):
    name = "web_scraper"
    description = "Scrape and extract text content from a given URL. Useful for getting detailed content from a specific web page."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to scrape",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of extracted text",
                    "default": 5000,
                },
            },
            "required": ["url"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        max_length = kwargs.get("max_length", 5000)

        if not url:
            return ToolResult(success=False, error="URL is required")

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; DeepResearch/1.0)",
                })
                resp.raise_for_status()

            text = _extract_text_from_html(resp.text)
            if len(text) > max_length:
                text = text[:max_length] + "..."

            return ToolResult(
                success=True,
                data={"url": url, "content": text, "length": len(text)},
            )
        except Exception as e:
            logger.error(f"Web scraping failed for {url}: {e}")
            return ToolResult(success=False, error=str(e))


def _extract_text_from_html(html: str) -> str:
    import re
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<[^>]+>', ' ', html)
    html = re.sub(r'\s+', ' ', html)
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return html.strip()
