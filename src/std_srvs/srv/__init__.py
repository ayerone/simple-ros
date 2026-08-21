import dataclasses


@dataclasses.dataclass
class _EmptyRequest:
    pass


@dataclasses.dataclass
class _EmptyResponse:
    pass


class Empty:
    Request = _EmptyRequest
    Response = _EmptyResponse
