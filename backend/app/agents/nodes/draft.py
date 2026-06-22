import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.draft import DRAFT_SYSTEM, DRAFT_USER

logger = logging.getLogger(__name__)


@register_node("draft")
class DraftNode(BaseNode):
    name = "draft"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        sources_text = "\n".join([f"- {s['title']}: {s['url']}" for s in state["sources"]])

        report = await chat_completion(
            messages=[
                {"role": "system", "content": DRAFT_SYSTEM},
                {"role": "user", "content": DRAFT_USER.format(
                    query=state["query"],
                    uploaded_context=state.get("uploaded_context") or state.get("media_context") or "",
                    synthesis=state["synthesis_text"],
                    sources=sources_text,
                )},
            ],
            api_key=state["api_key"],
            provider=state["provider"],
            model=state["model"],
            temperature=0.5,
        )

        logger.info("[Draft] Report drafted, length: %d", len(report))
        return self.emit(
            {**state, "report": report},
            "drafting",
            "报告撰写完成",
            95,
        )
