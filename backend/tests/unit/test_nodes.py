import pytest
from unittest.mock import AsyncMock, patch

from app.agents.nodes.planning import PlanningNode
from app.agents.nodes.search import SearchNode
from app.agents.nodes.filter import FilterNode
from app.agents.nodes.synthesis import SynthesisNode
from app.agents.nodes.draft import DraftNode
from app.agents.nodes.evaluate_quality import EvaluateQualityNode
from app.agents.nodes.evaluate_coverage import EvaluateCoverageNode
from app.agents.nodes.evaluate_report import EvaluateReportNode
from app.agents.nodes.refine_queries import RefineQueriesNode


class TestPlanningNode:
    @pytest.mark.asyncio
    async def test_execute_generates_sub_queries(self, base_state, mock_llm_response):
        with patch("app.agents.nodes.planning.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "1. AI applications in healthcare\n2. AI ethical concerns\n3. AI future trends"
            node = PlanningNode()
            result = await node.execute(base_state)

            assert "sub_queries" in result
            assert len(result["sub_queries"]) == 3
            assert result["current_step"] == "planning"
            assert len(result["steps"]) == 1

    @pytest.mark.asyncio
    async def test_execute_with_pdf_context(self, base_state, mock_llm_response):
        base_state["pdf_context"] = "Additional PDF content"
        with patch("app.agents.nodes.planning.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "1. Query one\n2. Query two"
            node = PlanningNode()
            result = await node.execute(base_state)

            call_args = mock_llm.call_args
            user_msg = call_args.kwargs.get("messages", call_args[0][0] if call_args[0] else [])[1]["content"]
            assert "Additional PDF content" in user_msg


class TestSearchNode:
    @pytest.mark.asyncio
    async def test_execute_searches_sub_queries(self, base_state, mock_search_results):
        base_state["sub_queries"] = ["AI in healthcare", "AI ethics"]
        with patch("app.agents.nodes.search.SearchService") as mock_svc_cls:
            mock_svc = mock_svc_cls.return_value
            mock_svc.search.return_value = mock_search_results
            node = SearchNode()
            result = await node.execute(base_state)

            assert "search_results" in result
            assert "sources" in result
            assert len(result["sources"]) > 0


class TestFilterNode:
    @pytest.mark.asyncio
    async def test_execute_filters_results(self, base_state, mock_search_results):
        base_state["sub_queries"] = ["AI in healthcare"]
        base_state["search_results"] = {"AI in healthcare": mock_search_results}
        with patch("app.agents.nodes.filter.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Filtered content about AI in healthcare"
            node = FilterNode()
            result = await node.execute(base_state)

            assert "filtered_content" in result
            assert "AI in healthcare" in result["filtered_content"]


class TestSynthesisNode:
    @pytest.mark.asyncio
    async def test_execute_synthesizes_content(self, base_state):
        base_state["filtered_content"] = {
            "AI in healthcare": "Content about AI in healthcare",
            "AI ethics": "Content about AI ethics",
        }
        with patch("app.agents.nodes.synthesis.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Synthesized analysis of AI"
            node = SynthesisNode()
            result = await node.execute(base_state)

            assert result["synthesis_text"] == "Synthesized analysis of AI"
            assert result["current_step"] == "synthesizing"


class TestDraftNode:
    @pytest.mark.asyncio
    async def test_execute_generates_report(self, base_state):
        base_state["synthesis_text"] = "Synthesized analysis"
        base_state["sources"] = [{"url": "https://example.com", "title": "Example"}]
        with patch("app.agents.nodes.draft.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "# AI Research Report\n\n## Executive Summary\n\nContent here"
            node = DraftNode()
            result = await node.execute(base_state)

            assert result["report"] == "# AI Research Report\n\n## Executive Summary\n\nContent here"
            assert result["current_step"] == "drafting"


class TestEvaluateQualityNode:
    @pytest.mark.asyncio
    async def test_quality_above_threshold(self, base_state, mock_search_results):
        base_state["sub_queries"] = ["AI in healthcare"]
        base_state["search_results"] = {"AI in healthcare": mock_search_results}
        with patch("app.agents.nodes.evaluate_quality.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"score": 8.0, "needs_refinement": false, "suggestions": []}'
            node = EvaluateQualityNode()
            result = await node.execute(base_state)

            assert result["quality_score"] == 8.0
            assert result["needs_refinement"] is False

    @pytest.mark.asyncio
    async def test_quality_below_threshold(self, base_state, mock_search_results):
        base_state["sub_queries"] = ["AI in healthcare"]
        base_state["search_results"] = {"AI in healthcare": mock_search_results}
        with patch("app.agents.nodes.evaluate_quality.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"score": 3.0, "needs_refinement": true, "suggestions": ["Add more specific queries"]}'
            node = EvaluateQualityNode()
            result = await node.execute(base_state)

            assert result["quality_score"] == 3.0
            assert result["needs_refinement"] is True


class TestEvaluateCoverageNode:
    @pytest.mark.asyncio
    async def test_coverage_sufficient(self, base_state):
        base_state["sub_queries"] = ["AI in healthcare", "AI ethics"]
        base_state["synthesis_text"] = "Comprehensive analysis"
        with patch("app.agents.nodes.evaluate_coverage.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"score": 8.5, "needs_more_research": false, "missing_aspects": []}'
            node = EvaluateCoverageNode()
            result = await node.execute(base_state)

            assert result["coverage_score"] == 8.5
            assert result["needs_more_research"] is False


class TestEvaluateReportNode:
    @pytest.mark.asyncio
    async def test_report_quality_good(self, base_state):
        base_state["report"] = "# Good Report\n\n## Summary\n\nWell-structured content"
        with patch("app.agents.nodes.evaluate_report.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"score": 8.0, "needs_revision": false, "suggestions": []}'
            node = EvaluateReportNode()
            result = await node.execute(base_state)

            assert result["report_quality"] == 8.0
            assert result["needs_revision"] is False

    @pytest.mark.asyncio
    async def test_empty_report(self, base_state):
        base_state["report"] = ""
        node = EvaluateReportNode()
        result = await node.execute(base_state)

        assert result["report_quality"] == 0.0
        assert result["needs_revision"] is False


class TestRefineQueriesNode:
    @pytest.mark.asyncio
    async def test_refines_queries(self, base_state):
        base_state["sub_queries"] = ["AI in healthcare"]
        base_state["refinement_suggestions"] = ["Add more specific queries about AI diagnosis"]
        with patch("app.agents.nodes.refine_queries.chat_completion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "1. AI diagnosis accuracy\n2. AI treatment recommendations"
            node = RefineQueriesNode()
            result = await node.execute(base_state)

            assert len(result["sub_queries"]) >= 1
