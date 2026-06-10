import json
import logging
from typing import Any

from app.agents.tools.registry import get_tool, get_all_tools
from app.agents.tools.base import ToolResult
from app.services.llm_service import chat_completion

logger = logging.getLogger(__name__)

TOOL_CALL_SYSTEM = """You are a research assistant with access to the following tools. Use them when needed to gather information and complete research tasks.

When you need to use a tool, respond with a JSON object containing:
- "tool_calls": a list of tool call objects, each with:
  - "name": the tool name
  - "arguments": an object with the tool's input parameters

If you don't need any tools, respond with:
- "response": your direct response text

Choose tools wisely - only call tools that are necessary for the task."""


class ToolExecutor:
    def __init__(self, tool_names: list[str] | None = None):
        if tool_names is None:
            tool_names = list(get_all_tools().keys())

        self.tools: dict[str, Any] = {}
        self.tool_schemas: list[dict] = []

        for name in tool_names:
            try:
                tool_cls = get_tool(name)
                self.tools[name] = tool_cls()
                self.tool_schemas.append(self.tools[name].to_openai_function())
            except KeyError:
                logger.warning(f"Tool '{name}' not found in registry, skipping")

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Tool '{tool_name}' not available")

        try:
            result = await tool.execute(**arguments)
            logger.info(f"[ToolExecutor] {tool_name} executed, success={result.success}")
            return result
        except Exception as e:
            logger.error(f"[ToolExecutor] {tool_name} failed: {e}")
            return ToolResult(success=False, error=str(e))

    async def run_with_tools(
        self,
        prompt: str,
        api_key: str,
        provider: str,
        model: str,
        max_rounds: int = 3,
        context: str = "",
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": TOOL_CALL_SYSTEM + "\n\nAvailable tools:\n" + json.dumps(self.tool_schemas, indent=2)},
            {"role": "user", "content": prompt + (f"\n\nAdditional context:\n{context}" if context else "")},
        ]

        all_tool_results: list[dict] = []
        final_response = ""

        for round_num in range(max_rounds):
            text = await chat_completion(
                messages=messages,
                api_key=api_key,
                provider=provider,
                model=model,
                temperature=0.3,
            )

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                final_response = text
                break

            if "response" in parsed:
                final_response = parsed["response"]
                break

            tool_calls = parsed.get("tool_calls", [])
            if not tool_calls:
                final_response = text
                break

            tool_results_text = ""
            for tc in tool_calls:
                tool_name = tc.get("name", "")
                arguments = tc.get("arguments", {})

                result = await self.execute_tool(tool_name, arguments)

                tool_result_entry = {
                    "tool": tool_name,
                    "arguments": arguments,
                    "success": result.success,
                    "data": result.data if result.success else None,
                    "error": result.error if not result.success else None,
                }
                all_tool_results.append(tool_result_entry)

                if result.success:
                    tool_results_text += f"\n[{tool_name}] Result: {json.dumps(result.data, ensure_ascii=False)[:2000]}\n"
                else:
                    tool_results_text += f"\n[{tool_name}] Error: {result.error}\n"

            messages.append({"role": "assistant", "content": text})
            messages.append({
                "role": "user",
                "content": f"Tool execution results:{tool_results_text}\n\nBased on these results, provide your response or call more tools if needed.",
            })

        if not final_response and all_tool_results:
            final_response = json.dumps(all_tool_results, ensure_ascii=False)

        return {
            "response": final_response,
            "tool_results": all_tool_results,
            "rounds_used": round_num + 1,
        }

    def get_tool_schemas(self) -> list[dict]:
        return self.tool_schemas
