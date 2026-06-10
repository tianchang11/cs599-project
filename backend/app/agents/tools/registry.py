from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.tools.base import BaseTool

_tool_registry: dict[str, type["BaseTool"]] = {}


def register_tool(name: str):
    def decorator(cls: type["BaseTool"]):
        _tool_registry[name] = cls
        cls.name = name
        return cls
    return decorator


def get_tool(name: str) -> type["BaseTool"]:
    if name not in _tool_registry:
        raise KeyError(f"Tool '{name}' not registered. Available: {list(_tool_registry.keys())}")
    return _tool_registry[name]


def get_all_tools() -> dict[str, type["BaseTool"]]:
    return dict(_tool_registry)
