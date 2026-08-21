import dataclasses


class ParameterType:
    PARAMETER_NOT_SET = 0
    PARAMETER_BOOL = 1
    PARAMETER_INTEGER = 2
    PARAMETER_DOUBLE = 3
    PARAMETER_STRING = 4


@dataclasses.dataclass
class ParameterValue:
    type: int = ParameterType.PARAMETER_NOT_SET
    bool_value: bool = False
    integer_value: int = 0
    double_value: float = 0.0
    string_value: str = ""


@dataclasses.dataclass
class Parameter:
    name: str = ""
    value: ParameterValue = dataclasses.field(default_factory=ParameterValue)


@dataclasses.dataclass
class SetParametersResult:
    successful: bool = False
    reason: str = ""
