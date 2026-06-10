import pytest
from app.agents.tools.web_search import WebSearchTool
from app.agents.tools.calculator import CalculatorTool
from app.agents.tools.base import ToolResult


class TestWebSearchTool:
    @pytest.mark.asyncio
    async def test_execute_with_empty_query(self):
        tool = WebSearchTool()
        result = await tool.execute(query="")
        assert result.success is False
        assert "required" in result.error.lower()

    def test_openai_function_schema(self):
        tool = WebSearchTool()
        schema = tool.to_openai_function()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "web_search"
        assert "query" in schema["function"]["parameters"]["properties"]


class TestCalculatorTool:
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="2 + 3")
        assert result.success is True
        assert result.data["result"] == 5

    @pytest.mark.asyncio
    async def test_complex_expression(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="sqrt(16) + 2 * 3")
        assert result.success is True
        assert result.data["result"] == 10.0

    @pytest.mark.asyncio
    async def test_percentage(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="100 * 0.15")
        assert result.success is True
        assert result.data["result"] == 15.0

    @pytest.mark.asyncio
    async def test_empty_expression(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_unsafe_expression(self):
        tool = CalculatorTool()
        result = await tool.execute(expression="__import__('os').system('ls')")
        assert result.success is False
