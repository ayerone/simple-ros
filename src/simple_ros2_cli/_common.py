"""Shared helpers used by more than one simple-ros2 verb."""

import dataclasses
import os
import re

import yaml


class _FieldYamlLoader(yaml.SafeLoader):
    """A YAML loader for message/service field arguments.

    PyYAML's default resolver follows YAML 1.1, which treats the bare words
    on/off/yes/no (in addition to true/false) as booleans. That's a real
    hazard here: turtlesim_msgs/srv/SetPen has a field literally named
    ``off``, so plain ``yaml.safe_load`` turns the mapping key ``off`` into
    the boolean ``False`` and ``cls(**kwargs)`` then blows up with
    "keywords must be strings". Restrict bool resolution to true/false
    (YAML 1.2's rule) so field names round-trip as the strings they are.
    """


_FieldYamlLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:bool"]
    for key, resolvers in _FieldYamlLoader.yaml_implicit_resolvers.items()
}
_FieldYamlLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def parse_field_yaml(text: str) -> dict:
    """Parse a CLI-supplied YAML mapping of message/request field values."""
    return yaml.load(text, Loader=_FieldYamlLoader) or {}


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
