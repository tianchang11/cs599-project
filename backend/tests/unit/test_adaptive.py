import pytest
from app.agents.adaptive import AdaptiveDepthController, DepthConfig


class TestAdaptiveDepthController:
    def test_factual_query_depth(self):
        ctrl = AdaptiveDepthController()
        result = ctrl.compute_initial_depth("What is the GDP of Japan?", "factual", 0.9)
        assert result["sub_queries_count"] == 3
        assert result["search_depth"] == 5

    def test_analytical_query_depth(self):
        ctrl = AdaptiveDepthController()
        result = ctrl.compute_initial_depth("What are the impacts of AI on employment?", "analytical", 0.8)
        assert result["sub_queries_count"] == 5
        assert result["search_depth"] == 8

    def test_exploratory_query_depth(self):
        ctrl = AdaptiveDepthController()
        result = ctrl.compute_initial_depth("Overview of quantum computing", "exploratory", 0.7)
        assert result["sub_queries_count"] == 7
        assert result["search_depth"] == 10

    def test_comparative_query_depth(self):
        ctrl = AdaptiveDepthController()
        result = ctrl.compute_initial_depth("React vs Vue vs Angular", "comparative", 0.85)
        assert result["sub_queries_count"] == 6
        assert result["search_depth"] == 8

    def test_low_confidence_increases_depth(self):
        ctrl = AdaptiveDepthController()
        high = ctrl.compute_initial_depth("Test query", "analytical", 0.9)
        low = ctrl.compute_initial_depth("Test query", "analytical", 0.3)
        assert low["sub_queries_count"] >= high["sub_queries_count"]
        assert low["search_depth"] >= high["search_depth"]

    def test_should_continue_iteration_below_max(self):
        ctrl = AdaptiveDepthController()
        should, reason = ctrl.should_continue_iteration(0, 4.0, 4.0)
        assert should is True

    def test_should_stop_at_max_iterations(self):
        ctrl = AdaptiveDepthController()
        should, reason = ctrl.should_continue_iteration(3, 4.0, 4.0)
        assert should is False
        assert "最大迭代" in reason

    def test_should_stop_when_thresholds_met(self):
        ctrl = AdaptiveDepthController()
        should, reason = ctrl.should_continue_iteration(1, 7.0, 7.0)
        assert should is False
        assert "达标" in reason

    def test_should_stop_on_diminishing_returns(self):
        ctrl = AdaptiveDepthController()
        should, reason = ctrl.should_continue_iteration(1, 5.2, 5.2, previous_quality=5.0, previous_coverage=5.0)
        assert should is False
        assert "递减" in reason

    def test_should_continue_draft(self):
        ctrl = AdaptiveDepthController()
        should, reason = ctrl.should_continue_draft(0, 5.0)
        assert should is True

    def test_should_stop_draft_at_max(self):
        ctrl = AdaptiveDepthController()
        should, reason = ctrl.should_continue_draft(2, 5.0)
        assert should is False

    def test_should_stop_draft_when_quality_met(self):
        ctrl = AdaptiveDepthController()
        should, reason = ctrl.should_continue_draft(0, 8.0)
        assert should is False

    def test_adjust_depth_for_first_iteration(self):
        ctrl = AdaptiveDepthController()
        result = ctrl.adjust_depth_for_iteration(0, 5.0, 5.0, 5, 8)
        assert result["sub_queries_count"] == 5
        assert result["search_depth"] == 8

    def test_adjust_depth_increases_on_deficit(self):
        ctrl = AdaptiveDepthController()
        result = ctrl.adjust_depth_for_iteration(1, 3.0, 3.0, 5, 8)
        assert result["sub_queries_count"] > 5
        assert result["search_depth"] > 8

    def test_adjust_depth_respects_max(self):
        config = DepthConfig(max_sub_queries=10, max_search_depth=15)
        ctrl = AdaptiveDepthController(config)
        result = ctrl.adjust_depth_for_iteration(1, 1.0, 1.0, 8, 12)
        assert result["sub_queries_count"] <= 10
        assert result["search_depth"] <= 15
