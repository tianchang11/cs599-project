import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_llm_response():
    return "1. Test sub-query one\n2. Test sub-query two\n3. Test sub-query three"


@pytest.fixture
def mock_search_results():
    from app.services.search_service import SearchResult
    return [
        SearchResult(
            url="https://example.com/1",
            title="Test Result 1",
            content="This is test content for result 1",
            score=0.95,
        ),
        SearchResult(
            url="https://example.com/2",
            title="Test Result 2",
            content="This is test content for result 2",
            score=0.85,
        ),
    ]


@pytest.fixture
def base_state():
    return {
        "query": "What is artificial intelligence?",
        "api_key": "test-api-key",
        "provider": "openai",
        "model": "gpt-4o",
        "pdf_context": "",
        "sub_queries": [],
        "search_results": {},
        "filtered_content": {},
        "synthesis_text": "",
        "report": "",
        "sources": [],
        "current_step": "planning",
        "steps": [],
        "iteration": 0,
        "draft_iteration": 0,
        "quality_score": 0.0,
        "coverage_score": 0.0,
        "report_quality": 0.0,
        "needs_refinement": False,
        "needs_more_research": False,
        "needs_revision": False,
        "refinement_suggestions": [],
        "missing_aspects": [],
        "revision_suggestions": [],
    }
