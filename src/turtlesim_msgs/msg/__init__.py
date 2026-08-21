import dataclasses


@dataclasses.dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    linear_velocity: float = 0.0
    angular_velocity: float = 0.0


@dataclasses.dataclass
class Color:
    r: int = 0
    g: int = 0
    b: int = 0
