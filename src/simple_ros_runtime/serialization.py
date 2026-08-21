"""Shared (de)serialization for message/request/response/parameter dataclasses.

``to_wire`` is a thin wrapper over ``dataclasses.asdict``. ``from_wire``
exists because a flat ``cls(**data)`` reconstruction leaves nested dataclass
fields (e.g. geometry_msgs/msg/Twist's ``linear``/``angular``) as plain dicts
instead of instances, which breaks the moment calling code does
``msg.linear.x``. Every message/request/response/goal/result/feedback type in
this project should go through these two functions rather than being
(de)serialized ad hoc at the call site.
"""

import dataclasses
import typing
from typing import Any, Type, TypeVar, get_type_hints

T = TypeVar("T")


def to_wire(instance: Any) -> dict:
    return dataclasses.asdict(instance)


def from_wire(cls: Type[T], data: dict) -> T:
    field_types = get_type_hints(cls)
    kwargs = {name: _reconstruct(field_types.get(name), value) for name, value in data.items()}
    return cls(**kwargs)


def _reconstruct(field_type: Any, value: Any) -> Any:
    if dataclasses.is_dataclass(field_type) and isinstance(value, dict):
        return from_wire(field_type, value)
    if typing.get_origin(field_type) is list and isinstance(value, list):
        (element_type,) = typing.get_args(field_type) or (None,)
        if dataclasses.is_dataclass(element_type):
            return [from_wire(element_type, item) if isinstance(item, dict) else item for item in value]
    return value
