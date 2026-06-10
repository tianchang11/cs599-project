import logging
from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.nodes.registry import get_node
from app.agents.strategies.base import ResearchStrategy, AnalyticalStrategy

logger = logging.getLogger(__name__)

_node_instances: dict[str, Any] = {}


def _get_node_instance(name: str):
    if name not in _node_instances:
        node_cls = get_node(name)
        _node_instances[name] = node_cls()
    return _node_instances[name]


def _make_node_wrapper(node_name: str):
    node = _get_node_instance(node_name)

    async def wrapper(state: dict[str, Any]) -> dict[str, Any]:
        return await node.execute(state)

    wrapper.__name__ = node_name
    return wrapper


def build_research_graph(strategy: ResearchStrategy | None = None):
    if strategy is None:
        strategy = AnalyticalStrategy()

    graph = StateGraph(dict)

    node_sequence = strategy.get_node_sequence()
    routing_rules = strategy.get_routing_rules()

    all_node_names = set(node_sequence)
    for rules in routing_rules.values():
        for rule in rules:
            target = rule["target"]
            if target != "__end__":
                all_node_names.add(target)

    for node_name in all_node_names:
        graph.add_node(node_name, _make_node_wrapper(node_name))

    graph.set_entry_point(node_sequence[0])

    for i, node_name in enumerate(node_sequence):
        if node_name in routing_rules:
            rules = routing_rules[node_name]

            def make_router(rules_list, strat, seq, idx):
                def router(state: dict[str, Any]) -> str:
                    iteration = state.get("iteration", 0)
                    draft_iteration = state.get("draft_iteration", 0)

                    for rule in rules_list:
                        condition = rule["condition"]
                        target = rule["target"]

                        if condition == "default":
                            continue

                        if condition == "needs_refinement":
                            if state.get("needs_refinement", False) and iteration < strat.max_iterations:
                                if state.get("should_continue_iteration", True):
                                    logger.info(f"[Router] {node_name} -> {target} (needs_refinement, iter={iteration})")
                                    return target
                            continue

                        if condition == "needs_more_research":
                            if state.get("needs_more_research", False) and iteration < strat.max_iterations:
                                if state.get("should_continue_iteration", True):
                                    logger.info(f"[Router] {node_name} -> {target} (needs_more_research, iter={iteration})")
                                    return target
                            continue

                        if condition == "needs_revision":
                            if state.get("needs_revision", False) and draft_iteration < 2:
                                logger.info(f"[Router] {node_name} -> {target} (needs_revision, draft_iter={draft_iteration})")
                                return target
                            continue

                        if condition == "quality_below_threshold":
                            quality_score = state.get("quality_score", 10.0)
                            if quality_score < strat.quality_threshold and iteration < strat.max_iterations:
                                logger.info(f"[Router] {node_name} -> {target} (quality={quality_score} < {strat.quality_threshold})")
                                return target
                            continue

                        if condition == "coverage_below_threshold":
                            coverage_score = state.get("coverage_score", 10.0)
                            if coverage_score < strat.coverage_threshold and iteration < strat.max_iterations:
                                logger.info(f"[Router] {node_name} -> {target} (coverage={coverage_score} < {strat.coverage_threshold})")
                                return target
                            continue

                        if condition == "report_below_threshold":
                            report_quality = state.get("report_quality", 10.0)
                            if report_quality < strat.report_quality_threshold and draft_iteration < 2:
                                logger.info(f"[Router] {node_name} -> {target} (report_quality={report_quality} < {strat.report_quality_threshold})")
                                return target
                            continue

                    for rule in rules_list:
                        if rule["condition"] == "default":
                            target = rule["target"]
                            resolved = END if target == "__end__" else target
                            logger.info(f"[Router] {node_name} -> {resolved} (default)")
                            return resolved

                    if idx + 1 < len(seq):
                        next_node = seq[idx + 1]
                        logger.info(f"[Router] {node_name} -> {next_node} (sequential fallback)")
                        return next_node

                    logger.info(f"[Router] {node_name} -> END (no more nodes)")
                    return END

                return router

            graph.add_conditional_edges(node_name, make_router(rules, strategy, node_sequence, i))
        else:
            if i + 1 < len(node_sequence):
                graph.add_edge(node_name, node_sequence[i + 1])
            else:
                graph.add_edge(node_name, END)

    compiled = graph.compile()
    compiled._strategy = strategy
    return compiled


research_graph = build_research_graph()
