import json
import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.evaluation import EVALUATE_REPORT_SYSTEM, EVALUATE_REPORT_USER

logger = logging.getLogger(__name__)


@register_node("evaluate_report")
class EvaluateReportNode(BaseNode):
    name = "evaluate_report"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        report = state.get("report", "")
        if not report:
            return self.emit(
                {**state, "report_quality": 0.0, "needs_revision": False},
                "evaluating",
                "报告为空，无法评估",
                97,
            )

        text = await chat_completion(
            messages=[
                {"role": "system", "content": EVALUATE_REPORT_SYSTEM},
                {"role": "user", "content": EVALUATE_REPORT_USER.format(
                    query=state["query"],
                    report=report[:4000],
                )},
            ],
            api_key=state["api_key"],
            provider=state["provider"],
            model=state["model"],
            temperature=0.3,
        )

        try:
            result = json.loads(text)
            report_quality = float(result.get("score", 0.5))
            needs_revision = result.get("needs_revision", False)
            revision_suggestions = result.get("suggestions", [])
        except (json.JSONDecodeError, ValueError):
            report_quality = 0.7
            needs_revision = False
            revision_suggestions = []

        report_quality_threshold = state.get("report_quality_threshold", 7.0)
        if report_quality < report_quality_threshold and not needs_revision:
            needs_revision = True
            revision_suggestions.append(f"报告质量评分({report_quality:.1f})低于阈值({report_quality_threshold})，建议修订")

        draft_iteration = state.get("draft_iteration", 0) + 1
        logger.info(f"[EvaluateReport] Score: {report_quality}, Needs revision: {needs_revision}, Draft iteration: {draft_iteration}")

        new_state = {
            **state,
            "report_quality": report_quality,
            "needs_revision": needs_revision,
            "revision_suggestions": revision_suggestions,
            "draft_iteration": draft_iteration,
        }

        if needs_revision and draft_iteration < 2:
            return self.emit(
                new_state,
                "evaluating",
                f"报告质量评分: {report_quality:.1f}/10，需要修订 (第{draft_iteration}轮)",
                97,
            )
        else:
            return self.emit(
                new_state,
                "evaluating",
                f"报告质量评分: {report_quality:.1f}/10，报告完成",
                100,
            )
