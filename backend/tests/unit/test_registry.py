import pytest
from app.agents.nodes.registry import register_node, get_node, get_all_nodes
from app.agents.nodes.base import BaseNode
from app.agents.tools.registry import register_tool, get_tool, get_all_tools
from app.agents.tools.base import BaseTool, ToolResult


class TestNodeRegistry:
    def test_registered_nodes_exist(self):
        nodes = get_all_nodes()
        expected = ["planning", "search", "filter", "synthesis", "draft",
                     "evaluate_quality", "evaluate_coverage", "evaluate_report",
                     "refine_queries"]
        for name in expected:
            assert name in nodes, f"Node '{name}' not registered"

    def test_get_node(self):
        node_cls = get_node("planning")
        assert node_cls.name == "planning"

    def test_get_nonexistent_node(self):
        with pytest.raises(KeyError):
            get_node("nonexistent_node")

    def test_register_custom_node(self):
        @register_node("test_custom")
        class CustomNode(BaseNode):
            async def execute(self, state):
                return state

        assert "test_custom" in get_all_nodes()
        node_cls = get_node("test_custom")
        assert node_cls.name == "test_custom"


class TestToolRegistry:
    def test_registered_tools_exist(self):
        tools = get_all_tools()
        expected = ["web_search", "web_scraper", "calculator", "academic_search"]
        for name in expected:
            assert name in tools, f"Tool '{name}' not registered"

    def test_get_tool(self):
        tool_cls = get_tool("web_search")
        assert tool_cls.name == "web_search"

    def test_get_nonexistent_tool(self):
        with pytest.raises(KeyError):
            get_tool("nonexistent_tool")

    def test_register_custom_tool(self):
        @register_tool("test_custom_tool")
        class CustomTool(BaseTool):
            async def execute(self, **kwargs):
                return ToolResult(success=True)

        assert "test_custom_tool" in get_all_tools()
