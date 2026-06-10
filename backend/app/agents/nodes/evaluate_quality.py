import json
import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.services.llm_service import chat_completion
from app.agents.prompts.evaluation import EVALUATE_QUALITY_SYSTEM, EVALUATE_QUALITY_USER

logger = logging.getLogger(__name__)


@register_node("evaluate_quality")
class EvaluateQualityNode(BaseNode):
    name = "evaluate_quality"

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        search_results_summary = ""
        for sq, hits in state.get("search_results", {}).items():
            search_results_summary += f"\n子查询: {sq}\n"
            for h in hits[:3]:
                search_results_summary += f"  - {h['title']} (score: {h.get('score', 'N/A')})\n"

        text = await chat_completion(
            messages=[
                {"role": "system", "content": EVALUATE_QUALITY_SYSTEM},
                {"role": "user", "content": EVALUATE_QUALITY_USER.format(
                    query=state["query"],
                    sub_queries=state.get("sub_queries", []),
                    search_results_summary=search_results_summary,
                )},
            ],
            api_key=state["api_key"],
            provider=state["provider"],
            model=state["model"],
            temperature=0.3,
        )

        try:
            result = json.loads(text)
            quality_score = float(result.get("score", 0.5))
            needs_refinement = result.get("needs_refinement", False)
            refinement_suggestions = result.get("suggestions", [])
        except (json.JSONDecodeError, ValueError):
            quality_score = 0.5
            needs_refinement = False
            refinement_suggestions = []

        quality_threshold = state.get("quality_threshold", 6.0)
        if quality_score < quality_threshold and not needs_refinement:
            needs_refinement = True
            refinement_suggestions.append(f"搜索质量评分({quality_score:.1f})低于阈值({quality_threshold})，建议优化搜索策略")

        iteration = state.get("iteration", 0) + 1
        logger.info(f"[EvaluateQuality] Score: {quality_score}, Needs refinement: {needs_refinement}, Iteration: {iteration}")

        new_state = {
            **state,
            "quality_score": quality_score,
            "needs_refinement": needs_refinement,
            "refinement_suggestions": refinement_suggestions,
            "iteration": iteration,
        }

        if needs_refinement and iteration < 3:
            return self.emit(
                new_state,
                "evaluating",
                f"搜索质量评分: {quality_score:.1f}/10，需要优化搜索策略 (第{iteration}轮)",
                42,
            )
        else:
            return self.emit(
                new_state,
                "evaluating",
                f"搜索质量评分: {quality_score:.1f}/10，质量达标，继续分析",
                42,
            )
