import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.synthesis import SYNTHESIS_SYSTEM, SYNTHESIS_USER

logger = logging.getLogger(__name__)


@register_node("synthesis")
class SynthesisNode(BaseNode):
    name = "synthesis"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        sub_content = "\n\n".join([
            f"=== 子查询: {sq} ===\n{content}"
            for sq, content in state["filtered_content"].items()
        ])

        synthesis = await chat_completion(
            messages=[
                {"role": "system", "content": SYNTHESIS_SYSTEM},
                {"role": "user", "content": SYNTHESIS_USER.format(query=state["query"], sub_content=sub_content)},
            ],
            api_key=state["api_key"],
            provider=state["provider"],
            model=state["model"],
            temperature=0.4,
        )

        logger.info("[Synthesis] Synthesis complete")
        return self.emit(
            {**state, "synthesis_text": synthesis},
            "synthesizing",
            "综合分析完成，正在撰写报告",
            75,
        )
