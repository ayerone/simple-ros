import dataclasses


@dataclasses.dataclass
class _AddTwoIntsRequest:
    a: int = 0
    b: int = 0


@dataclasses.dataclass
class _AddTwoIntsResponse:
    sum: int = 0


class AddTwoInts:
    Request = _AddTwoIntsRequest
    Response = _AddTwoIntsResponse
