import logging
from typing import Any

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.tools.registry import register_tool

logger = logging.getLogger(__name__)


@register_tool("calculator")
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate a mathematical expression. Supports basic arithmetic, percentages, and common math functions."

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', '100 * 0.15')",
                },
            },
            "required": ["expression"],
        }

    async def execute(self, **kwargs) -> ToolResult:
        expression = kwargs.get("expression", "")
        if not expression:
            return ToolResult(success=False, error="Expression is required")

        try:
            import math
            allowed_names = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "exp": math.exp, "pi": math.pi, "e": math.e,
                "ceil": math.ceil, "floor": math.floor,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
            }

            import re
            words = re.findall(r'[a-zA-Z_]\w*', expression)
            for word in words:
                if word not in allowed_names:
                    return ToolResult(success=False, error=f"Unsafe name in expression: {word}")

            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return ToolResult(success=True, data={"expression": expression, "result": result})
        except Exception as e:
            logger.error(f"Calculator failed: {e}")
            return ToolResult(success=False, error=str(e))
