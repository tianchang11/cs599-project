import logging
from typing import Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DepthConfig:
    initial_sub_queries: int = 5
    max_sub_queries: int = 10
    initial_search_depth: int = 8
    max_search_depth: int = 15
    quality_threshold: float = 6.0
    coverage_threshold: float = 6.0
    report_quality_threshold: float = 7.0
    max_iterations: int = 3
    max_draft_iterations: int = 2
    diminishing_returns_threshold: float = 0.5


class AdaptiveDepthController:
    def __init__(self, config: DepthConfig | None = None):
        self.config = config or DepthConfig()

    def compute_initial_depth(self, query: str, category: str, confidence: float) -> dict[str, Any]:
        base_sub_queries = self.config.initial_sub_queries
        base_search_depth = self.config.initial_search_depth

        if category == "factual":
            base_sub_queries = 3
            base_search_depth = 5
        elif category == "exploratory":
            base_sub_queries = 7
            base_search_depth = 10
        elif category == "comparative":
            base_sub_queries = 6
            base_search_depth = 8
        elif category == "analytical":
            base_sub_queries = 5
            base_search_depth = 8

        if confidence < 0.5:
            base_sub_queries = min(base_sub_queries + 2, self.config.max_sub_queries)
            base_search_depth = min(base_search_depth + 3, self.config.max_search_depth)

        query_length = len(query.split())
        if query_length > 20:
            base_sub_queries = min(base_sub_queries + 1, self.config.max_sub_queries)

        return {
            "sub_queries_count": base_sub_queries,
            "search_depth": base_search_depth,
            "category": category,
            "confidence": confidence,
        }

    def should_continue_iteration(
        self,
        iteration: int,
        quality_score: float,
        coverage_score: float,
        previous_quality: float | None = None,
        previous_coverage: float | None = None,
    ) -> tuple[bool, str]:
        if iteration >= self.config.max_iterations:
            return False, f"达到最大迭代次数 ({self.config.max_iterations})"

        if quality_score >= self.config.quality_threshold and coverage_score >= self.config.coverage_threshold:
            return False, f"质量({quality_score:.1f})和覆盖度({coverage_score:.1f})均达标"

        if previous_quality is not None and previous_coverage is not None:
            quality_gain = quality_score - previous_quality
            coverage_gain = coverage_score - previous_coverage

            if quality_gain < self.config.diminishing_returns_threshold and coverage_gain < self.config.diminishing_returns_threshold:
                return False, f"收益递减: 质量增益={quality_gain:.2f}, 覆盖度增益={coverage_gain:.2f}"

        return True, "继续迭代优化"

    def should_continue_draft(
        self,
        draft_iteration: int,
        report_quality: float,
        previous_report_quality: float | None = None,
    ) -> tuple[bool, str]:
        if draft_iteration >= self.config.max_draft_iterations:
            return False, f"达到最大修订次数 ({self.config.max_draft_iterations})"

        if report_quality >= self.config.report_quality_threshold:
            return False, f"报告质量({report_quality:.1f})达标"

        if previous_report_quality is not None:
            quality_gain = report_quality - previous_report_quality
            if quality_gain < self.config.diminishing_returns_threshold:
                return False, f"报告修订收益递减: 增益={quality_gain:.2f}"

        return True, "继续修订报告"

    def adjust_depth_for_iteration(
        self,
        iteration: int,
        quality_score: float,
        coverage_score: float,
        current_sub_queries: int,
        current_search_depth: int,
    ) -> dict[str, int]:
        if iteration == 0:
            return {
                "sub_queries_count": current_sub_queries,
                "search_depth": current_search_depth,
            }

        quality_deficit = max(0, self.config.quality_threshold - quality_score)
        coverage_deficit = max(0, self.config.coverage_threshold - coverage_score)

        extra_queries = min(int(quality_deficit), 3)
        extra_depth = min(int(coverage_deficit), 5)

        new_sub_queries = min(current_sub_queries + extra_queries, self.config.max_sub_queries)
        new_search_depth = min(current_search_depth + extra_depth, self.config.max_search_depth)

        logger.info(
            f"[AdaptiveDepth] Iteration {iteration}: "
            f"sub_queries {current_sub_queries}->{new_sub_queries}, "
            f"search_depth {current_search_depth}->{new_search_depth}"
        )

        return {
            "sub_queries_count": new_sub_queries,
            "search_depth": new_search_depth,
        }
