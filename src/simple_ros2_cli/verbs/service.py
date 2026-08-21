import sys

import yaml

import rclpy
from rclpy.executors import spin_until_future_complete
from rclpy.node import Node
from simple_ros_runtime import registry
from simple_ros_runtime.errors import ros_error
from simple_ros_runtime.serialization import from_wire
from simple_ros2_cli._common import ephemeral_node_name, resolve_type


def run(argv: list) -> int:
    if not argv:
        _usage()
        return 1
    verb, rest = argv[0], argv[1:]
    if verb == "list":
        return _list(rest)
    if verb == "type" and rest:
        return _type(rest[0])
    if verb == "call" and len(rest) >= 2:
        return _call(rest)
    if verb == "info" and rest:
        return _info(rest[0])
    _usage()
    return 1


def _usage() -> None:
    print("usage: simple-ros2 service <list [-t]|type SERVICE|call SERVICE TYPE [YAML]|info SERVICE>", file=sys.stderr)


def _collect_services() -> dict:
    services = {}
    for info in registry.scan_nodes():
        for entry in info.services:
            services[entry["name"]] = entry["type"]
    return services


def _list(rest: list) -> int:
    show_types = "-t" in rest or "--show-types" in rest
    for name, type_name in sorted(_collect_services().items()):
        print(f"{name} [{type_name}]" if show_types else name)
    return 0


def _type(name: str) -> int:
    services = _collect_services()
    if name not in services:
        print(ros_error(f"Unknown service '{name}'", "check 'simple-ros2 service list' for the exact name"), file=sys.stderr)
        return 1
    print(services[name])
    return 0


def _info(name: str) -> int:
    server_count = sum(1 for info in registry.scan_nodes() for entry in info.services if entry["name"] == name)
    services = _collect_services()
    if name not in services:
        print(ros_error(f"Unknown service '{name}'", "check 'simple-ros2 service list' for the exact name"), file=sys.stderr)
        return 1
    print(f"Type: {services[name]}")
    print("Clients count: 0")
    print(f"Services count: {server_count}")
    return 0


def _call(rest: list) -> int:
    name, type_name, *values = rest
    yaml_args = values[0] if values else "{}"
    srv_type = resolve_type(type_name)
    request = from_wire(srv_type.Request, yaml.safe_load(yaml_args) or {})

    with rclpy.init(args=[]):
        node = Node(ephemeral_node_name())
        client = node.create_client(srv_type, name)
        if not client.wait_for_service(timeout_sec=5.0):
            print(ros_error(f"service not available: {name}", "check 'simple-ros2 service list' and that the server node is actually running"), file=sys.stderr)
            node.destroy_node()
            return 1
        print(f"requester: making request: {request}\n")
        future = client.call_async(request)
        spin_until_future_complete(node, future, timeout_sec=5.0)
        if not future.done():
            print(ros_error("service call timed out", "the server may be stuck; check its terminal for errors"), file=sys.stderr)
            node.destroy_node()
            return 1
        print("response:")
        print(future.result())
        node.destroy_node()
    return 0
