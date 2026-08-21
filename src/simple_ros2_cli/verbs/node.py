import sys

from simple_ros_runtime import registry
from simple_ros_runtime.errors import ros_error


def run(argv: list) -> int:
    if not argv or argv[0] == "list":
        for info in registry.scan_nodes():
            print(f"/{info.name}")
        return 0
    if argv[0] == "info" and len(argv) > 1:
        return _info(argv[1])
    print("usage: simple-ros2 node <list|info NODE_NAME>", file=sys.stderr)
    return 1


def _info(name: str) -> int:
    name = name.lstrip("/")
    matches = [n for n in registry.scan_nodes() if n.name == name]
    if not matches:
        print(ros_error(f"Unable to find node '{name}'", "check 'simple-ros2 node list' for the exact name"), file=sys.stderr)
        return 1
    info = matches[0]
    print(f"/{info.name}")
    print("  Subscribers:")
    for entry in info.subscriptions:
        print(f"    {entry['topic']}: {entry['type']}")
    print("  Publishers:")
    for entry in info.publications:
        print(f"    {entry['topic']}: {entry['type']}")
    print("  Service Servers:")
    for entry in info.services:
        print(f"    {entry['name']}: {entry['type']}")
    print("  Service Clients:")
    for entry in info.service_clients:
        print(f"    {entry['name']}: {entry['type']}")
    return 0
