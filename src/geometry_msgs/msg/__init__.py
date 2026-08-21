import dataclasses


@dataclasses.dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclasses.dataclass
class Point:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclasses.dataclass
class Twist:
    linear: Vector3 = dataclasses.field(default_factory=Vector3)
    angular: Vector3 = dataclasses.field(default_factory=Vector3)
