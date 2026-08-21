import sys

import rclpy
from rclpy.executors import spin_until_future_complete
from rclpy.node import Node
from simple_ros_runtime import registry
from simple_ros_runtime.errors import ros_error
from simple_ros2_cli._common import ephemeral_node_name

_TYPE_LABEL = {}
_VALUE_FIELD = {}
_CONVERTER = {}


def _lazy_type_tables():
    if _TYPE_LABEL:
        return
    from rcl_interfaces.msg import ParameterType

    _TYPE_LABEL.update(
        {
            ParameterType.PARAMETER_INTEGER: "Integer",
            ParameterType.PARAMETER_DOUBLE: "Double",
            ParameterType.PARAMETER_BOOL: "Boolean",
            ParameterType.PARAMETER_STRING: "String",
        }
    )
    _VALUE_FIELD.update(
        {
            ParameterType.PARAMETER_INTEGER: "integer_value",
            ParameterType.PARAMETER_DOUBLE: "double_value",
            ParameterType.PARAMETER_BOOL: "bool_value",
            ParameterType.PARAMETER_STRING: "string_value",
        }
    )
    _CONVERTER.update(
        {
            ParameterType.PARAMETER_INTEGER: int,
            ParameterType.PARAMETER_DOUBLE: float,
            ParameterType.PARAMETER_BOOL: lambda s: s.lower() in ("true", "1", "yes"),
            ParameterType.PARAMETER_STRING: str,
        }
    )


def run(argv: list) -> int:
    if not argv or argv[0] == "list":
        return _list()
    if argv[0] == "get" and len(argv) >= 3:
        return _get(argv[1], argv[2])
    if argv[0] == "set" and len(argv) >= 4:
        return _set(argv[1], argv[2], argv[3])
    print("usage: simple-ros2 param <list|get NODE PARAM|set NODE PARAM VALUE>", file=sys.stderr)
    return 1


def _list() -> int:
    for info in registry.scan_nodes():
        if not info.parameters:
            continue
        print(f"/{info.name}:")
        for name in sorted(info.parameters):
            print(f"  {name}")
    return 0


def _make_param_client(node, node_name):
    from rcl_interfaces.srv import GetParameters, SetParameters

    return node.create_client(GetParameters, f"{node_name}/get_parameters"), node.create_client(SetParameters, f"{node_name}/set_parameters")


def _get(node_name: str, param_name: str) -> int:
    _lazy_type_tables()
    from rcl_interfaces.srv import GetParameters

    with rclpy.init(args=[]):
        node = Node(ephemeral_node_name())
        client = node.create_client(GetParameters, f"{node_name}/get_parameters")
        if not client.wait_for_service(timeout_sec=5.0):
            print(ros_error(f"Node not found: '{node_name}'", "check 'simple-ros2 node list' for the exact name"), file=sys.stderr)
            node.destroy_node()
            return 1
        future = client.call_async(GetParameters.Request(names=[param_name]))
        spin_until_future_complete(node, future, timeout_sec=5.0)
        value = future.result().values[0]
        label = _TYPE_LABEL.get(value.type, "String")
        val = getattr(value, _VALUE_FIELD.get(value.type, "string_value"))
        print(f"{label} value is: {val}")
        node.destroy_node()
    return 0


def _set(node_name: str, param_name: str, value_str: str) -> int:
    _lazy_type_tables()
    from rcl_interfaces.msg import Parameter as WireParameter
    from rcl_interfaces.msg import ParameterValue
    from rcl_interfaces.srv import GetParameters, SetParameters

    with rclpy.init(args=[]):
        node = Node(ephemeral_node_name())
        get_client, set_client = _make_param_client(node, node_name)
        if not get_client.wait_for_service(timeout_sec=5.0) or not set_client.wait_for_service(timeout_sec=5.0):
            print(ros_error(f"Node not found: '{node_name}'", "check 'simple-ros2 node list' for the exact name"), file=sys.stderr)
            node.destroy_node()
            return 1

        get_future = get_client.call_async(GetParameters.Request(names=[param_name]))
        spin_until_future_complete(node, get_future, timeout_sec=5.0)
        current_type = get_future.result().values[0].type

        converter = _CONVERTER.get(current_type, str)
        value_field = _VALUE_FIELD.get(current_type, "string_value")
        new_value = converter(value_str)

        wire_value = ParameterValue(type=current_type)
        setattr(wire_value, value_field, new_value)
        set_future = set_client.call_async(SetParameters.Request(parameters=[WireParameter(name=param_name, value=wire_value)]))
        spin_until_future_complete(node, set_future, timeout_sec=5.0)
        result = set_future.result().results[0]
        if result.successful:
            print("Set parameter successful")
        else:
            print(f"Set parameter {param_name} failed: {result.reason}")
        node.destroy_node()
    return 0
