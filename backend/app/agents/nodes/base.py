from abc import ABC, abstractmethod
from typing import Any


class BaseNode(ABC):
    name: str = ""

    @abstractmethod
    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        ...

    def emit(self, state: dict[str, Any], step: str, message: str, percent: int | None = None) -> dict[str, Any]:
        steps = list(state.get("steps") or [])
        steps.append({"step": step, "message": message, "percent": percent})
        return {
            **state,
            "current_step": step,
            "steps": steps,
        }
