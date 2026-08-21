"""rclpy.parameter.Parameter / Parameter.Type -- matches real rclpy's API."""

import enum
from typing import Any


class Parameter:
    class Type(enum.Enum):
        NOT_SET = 0
        BOOL = 1
        INTEGER = 2
        DOUBLE = 3
        STRING = 4

    def __init__(self, name: str, type_: "Parameter.Type" = None, value: Any = None):
        self.name = name
        self.type_ = type_ if type_ is not None else infer_parameter_type(value)
        self.value = value

    def get_parameter_value(self) -> "ParameterValue":
        return ParameterValue(self.type_, self.value)

    def __repr__(self):
        return f"Parameter(name={self.name!r}, type_={self.type_}, value={self.value!r})"


class ParameterValue:
    def __init__(self, type_: "Parameter.Type", value: Any):
        self.type = type_
        self._value = value

    @property
    def string_value(self) -> str:
        return self._value if self.type == Parameter.Type.STRING else ""

    @property
    def integer_value(self) -> int:
        return self._value if self.type == Parameter.Type.INTEGER else 0

    @property
    def double_value(self) -> float:
        return self._value if self.type == Parameter.Type.DOUBLE else 0.0

    @property
    def bool_value(self) -> bool:
        return self._value if self.type == Parameter.Type.BOOL else False


def infer_parameter_type(value: Any) -> "Parameter.Type":
    # bool before int: bool is a subclass of int in Python.
    if isinstance(value, bool):
        return Parameter.Type.BOOL
    if isinstance(value, int):
        return Parameter.Type.INTEGER
    if isinstance(value, float):
        return Parameter.Type.DOUBLE
    if isinstance(value, str):
        return Parameter.Type.STRING
    return Parameter.Type.NOT_SET
