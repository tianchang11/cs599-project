import pytest
from app.agents.strategies.base import (
    FactualStrategy,
    AnalyticalStrategy,
    ExploratoryStrategy,
    ComparativeStrategy,
    get_strategy,
    STRATEGIES,
)


class TestFactualStrategy:
    def test_node_sequence(self):
        s = FactualStrategy()
        assert s.get_node_sequence() == ["planning", "search", "filter", "synthesis", "draft"]

    def test_no_routing_rules(self):
        s = FactualStrategy()
        assert s.get_routing_rules() == {}

    def test_max_iterations(self):
        s = FactualStrategy()
        assert s.max_iterations == 1


class TestAnalyticalStrategy:
    def test_node_sequence(self):
        s = AnalyticalStrategy()
        seq = s.get_node_sequence()
        assert "evaluate_quality" in seq
        assert "evaluate_coverage" in seq
        assert "evaluate_report" in seq

    def test_routing_rules(self):
        s = AnalyticalStrategy()
        rules = s.get_routing_rules()
        assert "evaluate_quality" in rules
        assert "evaluate_coverage" in rules
        assert "evaluate_report" in rules

    def test_max_iterations(self):
        s = AnalyticalStrategy()
        assert s.max_iterations == 3


class TestExploratoryStrategy:
    def test_node_sequence(self):
        s = ExploratoryStrategy()
        seq = s.get_node_sequence()
        assert "evaluate_quality" in seq
        assert "evaluate_coverage" in seq

    def test_max_sub_queries(self):
        s = ExploratoryStrategy()
        assert s.max_sub_queries == 7


class TestComparativeStrategy:
    def test_node_sequence(self):
        s = ComparativeStrategy()
        seq = s.get_node_sequence()
        assert "evaluate_quality" in seq
        assert "evaluate_report" in seq


class TestGetStrategy:
    def test_get_existing_strategy(self):
        for name in STRATEGIES:
            strategy = get_strategy(name)
            assert strategy.name == name

    def test_get_nonexistent_strategy(self):
        with pytest.raises(KeyError):
            get_strategy("nonexistent")
