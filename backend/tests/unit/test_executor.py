import pytest
from app.agents.tools.executor import ToolExecutor
from app.agents.tools.calculator import CalculatorTool
from app.agents.tools.base import ToolResult


class TestToolExecutor:
    def test_init_with_all_tools(self):
        executor = ToolExecutor()
        assert "web_search" in executor.tools
        assert "calculator" in executor.tools
        assert "web_scraper" in executor.tools
        assert "academic_search" in executor.tools

    def test_init_with_specific_tools(self):
        executor = ToolExecutor(tool_names=["calculator"])
        assert "calculator" in executor.tools
        assert "web_search" not in executor.tools

    def test_init_with_nonexistent_tool(self):
        executor = ToolExecutor(tool_names=["calculator", "nonexistent"])
        assert "calculator" in executor.tools
        assert "nonexistent" not in executor.tools

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        executor = ToolExecutor(tool_names=["calculator"])
        result = await executor.execute_tool("calculator", {"expression": "2 + 3"})
        assert result.success is True
        assert result.data["result"] == 5

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        executor = ToolExecutor(tool_names=["calculator"])
        result = await executor.execute_tool("nonexistent", {})
        assert result.success is False

    def test_get_tool_schemas(self):
        executor = ToolExecutor(tool_names=["calculator"])
        schemas = executor.get_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "calculator"
