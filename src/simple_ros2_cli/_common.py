"""Shared helpers used by more than one simple-ros2 verb."""

import dataclasses
import os


def resolve_type(type_name: str) -> type:
    package, kind, cls_name = type_name.split("/")
    module = __import__(f"{package}.{kind}", fromlist=[cls_name])
    return getattr(module, cls_name)


def ephemeral_node_name() -> str:
    # Matches the naming convention shown in the tutorials for CLI-spawned
    # nodes, e.g. "/_ros2cli_26646" created by `ros2 topic echo`.
    return f"_ros2cli_{os.getpid()}"


def format_yaml(value, indent: int = 0) -> str:
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    prefix = "  " * indent
    if isinstance(value, dict):
        lines = []
        for key, val in value.items():
            if isinstance(val, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(format_yaml(val, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {val}")
        return "\n".join(lines)
    return f"{prefix}{value}"
