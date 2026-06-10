from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        ...

    def to_openai_function(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters(),
            },
        }

    def get_parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}
