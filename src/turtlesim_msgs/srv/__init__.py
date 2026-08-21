import dataclasses


@dataclasses.dataclass
class _SpawnRequest:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    name: str = ""


@dataclasses.dataclass
class _SpawnResponse:
    name: str = ""


class Spawn:
    Request = _SpawnRequest
    Response = _SpawnResponse


@dataclasses.dataclass
class _KillRequest:
    name: str = ""


@dataclasses.dataclass
class _KillResponse:
    pass


class Kill:
    Request = _KillRequest
    Response = _KillResponse


@dataclasses.dataclass
class _SetPenRequest:
    r: int = 0
    g: int = 0
    b: int = 0
    width: int = 0
    off: int = 0


@dataclasses.dataclass
class _SetPenResponse:
    pass


class SetPen:
    Request = _SetPenRequest
    Response = _SetPenResponse


@dataclasses.dataclass
class _TeleportAbsoluteRequest:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


@dataclasses.dataclass
class _TeleportAbsoluteResponse:
    pass


class TeleportAbsolute:
    Request = _TeleportAbsoluteRequest
    Response = _TeleportAbsoluteResponse


@dataclasses.dataclass
class _TeleportRelativeRequest:
    linear: float = 0.0
    angular: float = 0.0


@dataclasses.dataclass
class _TeleportRelativeResponse:
    pass


class TeleportRelative:
    Request = _TeleportRelativeRequest
    Response = _TeleportRelativeResponse
