import dataclasses

from simple_ros_runtime.serialization import from_wire, to_wire


@dataclasses.dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclasses.dataclass
class Twist:
    linear: Vector3 = dataclasses.field(default_factory=Vector3)
    angular: Vector3 = dataclasses.field(default_factory=Vector3)


@dataclasses.dataclass
class StringMsg:
    data: str = ""


def test_flat_dataclass_roundtrip():
    msg = StringMsg(data="hello world")
    wire = to_wire(msg)
    assert wire == {"data": "hello world"}
    restored = from_wire(StringMsg, wire)
    assert restored == msg


@dataclasses.dataclass
class NamedValue:
    name: str = ""
    value: float = 0.0


@dataclasses.dataclass
class ValueList:
    entries: list[NamedValue] = dataclasses.field(default_factory=list)


def test_list_of_dataclass_field_reconstructs_real_instances():
    # Same bug class as the nested-single-field case, just inside a list:
    # rcl_interfaces' GetParameters/SetParameters services carry
    # List[Parameter]/List[ParameterValue], and a naive from_wire would
    # leave each list entry as a dict instead of a real instance.
    msg = ValueList(entries=[NamedValue(name="a", value=1.0), NamedValue(name="b", value=2.0)])
    wire = to_wire(msg)
    restored = from_wire(ValueList, wire)
    assert all(isinstance(entry, NamedValue) for entry in restored.entries)
    assert restored == msg


def test_nested_dataclass_roundtrip_reconstructs_real_instances():
    # This is the case a flat cls(**data) reconstruction silently breaks:
    # .linear must be a real Vector3, not a dict, or msg.linear.x raises.
    msg = Twist(linear=Vector3(x=2.0), angular=Vector3(z=1.8))
    wire = to_wire(msg)
    assert wire == {
        "linear": {"x": 2.0, "y": 0.0, "z": 0.0},
        "angular": {"x": 0.0, "y": 0.0, "z": 1.8},
    }
    restored = from_wire(Twist, wire)
    assert isinstance(restored.linear, Vector3)
    assert isinstance(restored.angular, Vector3)
    assert restored.linear.x == 2.0
    assert restored.angular.z == 1.8
    assert restored == msg
