from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.nodes.base import BaseNode

_node_registry: dict[str, type["BaseNode"]] = {}


def register_node(name: str):
    def decorator(cls: type["BaseNode"]):
        _node_registry[name] = cls
        cls.name = name
        return cls
    return decorator


def get_node(name: str) -> type["BaseNode"]:
    if name not in _node_registry:
        raise KeyError(f"Node '{name}' not registered. Available: {list(_node_registry.keys())}")
    return _node_registry[name]


def get_all_nodes() -> dict[str, type["BaseNode"]]:
    return dict(_node_registry)
