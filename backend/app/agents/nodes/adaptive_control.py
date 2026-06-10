import logging
from typing import Any

from app.agents.nodes.base import BaseNode
from app.agents.nodes.registry import register_node
from app.agents.adaptive import AdaptiveDepthController, DepthConfig

logger = logging.getLogger(__name__)


@register_node("adaptive_control")
class AdaptiveControlNode(BaseNode):
    name = "adaptive_control"

    def __init__(self):
        self.controller = AdaptiveDepthController()

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        iteration = state.get("iteration", 0)
        quality_score = state.get("quality_score", 0.0)
        coverage_score = state.get("coverage_score", 0.0)
        report_quality = state.get("report_quality", 0.0)
        draft_iteration = state.get("draft_iteration", 0)

        previous_quality = state.get("_previous_quality")
        previous_coverage = state.get("_previous_coverage")

        if iteration > 0 and previous_quality is None:
            previous_quality = 0.0
            previous_coverage = 0.0

        should_continue, reason = self.controller.should_continue_iteration(
            iteration=iteration,
            quality_score=quality_score,
            coverage_score=coverage_score,
            previous_quality=previous_quality,
            previous_coverage=previous_coverage,
        )

        depth_adjustment = self.controller.adjust_depth_for_iteration(
            iteration=iteration,
            quality_score=quality_score,
            coverage_score=coverage_score,
            current_sub_queries=state.get("max_sub_queries", 5),
            current_search_depth=state.get("search_depth", 8),
        )

        new_state = {
            **state,
            "_previous_quality": quality_score,
            "_previous_coverage": coverage_score,
            "max_sub_queries": depth_adjustment["sub_queries_count"],
            "search_depth": depth_adjustment["search_depth"],
            "should_continue_iteration": should_continue,
            "termination_reason": reason if not should_continue else None,
        }

        if should_continue:
            return self.emit(
                new_state,
                "evaluating",
                f"迭代评估: 质量={quality_score:.1f}, 覆盖度={coverage_score:.1f}, 继续优化",
                45,
            )
        else:
            return self.emit(
                new_state,
                "evaluating",
                f"迭代终止: {reason}",
                45,
            )
