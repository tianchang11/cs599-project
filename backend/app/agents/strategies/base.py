from abc import ABC, abstractmethod
from typing import Any


class ResearchStrategy(ABC):
    name: str = ""
    description: str = ""

    max_iterations: int = 2
    max_sub_queries: int = 5
    search_depth: int = 8
    quality_threshold: float = 6.0
    coverage_threshold: float = 6.0
    report_quality_threshold: float = 7.0

    @abstractmethod
    def get_node_sequence(self) -> list[str]:
        ...

    @abstractmethod
    def get_routing_rules(self) -> dict[str, list[dict]]:
        ...


class FactualStrategy(ResearchStrategy):
    name = "factual"
    description = "快速事实查询，单轮搜索直接回答"
    max_iterations = 1
    max_sub_queries = 3
    search_depth = 5
    quality_threshold = 5.0
    coverage_threshold = 5.0
    report_quality_threshold = 6.0

    def get_node_sequence(self) -> list[str]:
        return ["planning", "search", "filter", "synthesis", "draft"]

    def get_routing_rules(self) -> dict[str, list[dict]]:
        return {}


class AnalyticalStrategy(ResearchStrategy):
    name = "analytical"
    description = "深度分析查询，多源检索与迭代优化"
    max_iterations = 3
    max_sub_queries = 5
    search_depth = 8
    quality_threshold = 6.0
    coverage_threshold = 6.0
    report_quality_threshold = 7.0

    def get_node_sequence(self) -> list[str]:
        return [
            "planning", "tool_search", "evaluate_quality", "adaptive_control",
            "filter", "synthesis", "evaluate_coverage", "draft", "evaluate_report",
        ]

    def get_routing_rules(self) -> dict[str, list[dict]]:
        return {
            "evaluate_quality": [
                {"condition": "needs_refinement", "target": "refine_queries"},
                {"condition": "default", "target": "adaptive_control"},
            ],
            "adaptive_control": [
                {"condition": "needs_refinement", "target": "refine_queries"},
                {"condition": "default", "target": "filter"},
            ],
            "evaluate_coverage": [
                {"condition": "needs_more_research", "target": "planning"},
                {"condition": "default", "target": "draft"},
            ],
            "evaluate_report": [
                {"condition": "needs_revision", "target": "draft"},
                {"condition": "default", "target": "__end__"},
            ],
            "refine_queries": [
                {"condition": "default", "target": "tool_search"},
            ],
        }


class ExploratoryStrategy(ResearchStrategy):
    name = "exploratory"
    description = "探索性查询，广泛搜索发现主题"
    max_iterations = 2
    max_sub_queries = 7
    search_depth = 10
    quality_threshold = 5.0
    coverage_threshold = 5.0
    report_quality_threshold = 6.0

    def get_node_sequence(self) -> list[str]:
        return [
            "planning", "tool_search", "evaluate_quality", "adaptive_control",
            "filter", "synthesis", "evaluate_coverage", "draft",
        ]

    def get_routing_rules(self) -> dict[str, list[dict]]:
        return {
            "evaluate_quality": [
                {"condition": "needs_refinement", "target": "refine_queries"},
                {"condition": "default", "target": "adaptive_control"},
            ],
            "adaptive_control": [
                {"condition": "needs_refinement", "target": "refine_queries"},
                {"condition": "default", "target": "filter"},
            ],
            "evaluate_coverage": [
                {"condition": "needs_more_research", "target": "planning"},
                {"condition": "default", "target": "draft"},
            ],
            "refine_queries": [
                {"condition": "default", "target": "tool_search"},
            ],
        }


class ComparativeStrategy(ResearchStrategy):
    name = "comparative"
    description = "比较性查询，对比检索与表格生成"
    max_iterations = 2
    max_sub_queries = 6
    search_depth = 8
    quality_threshold = 6.0
    coverage_threshold = 6.0
    report_quality_threshold = 7.0

    def get_node_sequence(self) -> list[str]:
        return [
            "planning", "tool_search", "evaluate_quality", "adaptive_control",
            "filter", "synthesis", "draft", "evaluate_report",
        ]

    def get_routing_rules(self) -> dict[str, list[dict]]:
        return {
            "evaluate_quality": [
                {"condition": "needs_refinement", "target": "refine_queries"},
                {"condition": "default", "target": "adaptive_control"},
            ],
            "adaptive_control": [
                {"condition": "needs_refinement", "target": "refine_queries"},
                {"condition": "default", "target": "filter"},
            ],
            "evaluate_report": [
                {"condition": "needs_revision", "target": "draft"},
                {"condition": "default", "target": "__end__"},
            ],
            "refine_queries": [
                {"condition": "default", "target": "tool_search"},
            ],
        }


STRATEGIES: dict[str, type[ResearchStrategy]] = {
    "factual": FactualStrategy,
    "analytical": AnalyticalStrategy,
    "exploratory": ExploratoryStrategy,
    "comparative": ComparativeStrategy,
}


def get_strategy(name: str) -> ResearchStrategy:
    if name not in STRATEGIES:
        raise KeyError(f"Strategy '{name}' not found. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]()
