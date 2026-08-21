import dataclasses

from rcl_interfaces.msg import Parameter, ParameterValue, SetParametersResult


@dataclasses.dataclass
class _GetParametersRequest:
    names: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class _GetParametersResponse:
    values: list[ParameterValue] = dataclasses.field(default_factory=list)


class GetParameters:
    Request = _GetParametersRequest
    Response = _GetParametersResponse


@dataclasses.dataclass
class _SetParametersRequest:
    parameters: list[Parameter] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class _SetParametersResponse:
    results: list[SetParametersResult] = dataclasses.field(default_factory=list)


class SetParameters:
    Request = _SetParametersRequest
    Response = _SetParametersResponse
