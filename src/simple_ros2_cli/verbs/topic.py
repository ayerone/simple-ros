import argparse
import sys
import time

import yaml

import rclpy
from rclpy.node import Node
from simple_ros_runtime import registry
from simple_ros_runtime.errors import ros_error
from simple_ros_runtime.serialization import from_wire
from simple_ros2_cli._common import ephemeral_node_name, format_yaml, resolve_type


def run(argv: list) -> int:
    if not argv:
        _usage()
        return 1
    verb, rest = argv[0], argv[1:]
    if verb == "list":
        return _list(rest)
    if verb == "echo":
        return _echo(rest)
    if verb == "info":
        return _info(rest)
    if verb == "pub":
        return _pub(rest)
    _usage()
    return 1


def _usage() -> None:
    print("usage: simple-ros2 topic <list [-t]|echo TOPIC|info TOPIC [--verbose]|pub [--once] [-w N] [--rate N] TOPIC TYPE [YAML]>", file=sys.stderr)


def _collect_topics() -> dict:
    topics = {}
    for info in registry.scan_nodes():
        for entry in info.publications + info.subscriptions:
            topics[entry["topic"]] = entry["type"]
    return topics


def _list(rest: list) -> int:
    show_types = "-t" in rest or "--show-types" in rest
    for topic, type_name in sorted(_collect_topics().items()):
        print(f"{topic} [{type_name}]" if show_types else topic)
    return 0


def _info(rest: list) -> int:
    if not rest:
        _usage()
        return 1
    topic = rest[0]
    verbose = "--verbose" in rest or "-v" in rest
    publishers, subscribers, type_name = [], [], None
    for info in registry.scan_nodes():
        for entry in info.publications:
            if entry["topic"] == topic:
                publishers.append(info)
                type_name = entry["type"]
        for entry in info.subscriptions:
            if entry["topic"] == topic:
                subscribers.append(info)
                type_name = entry["type"]
    if type_name is None:
        print(ros_error(f"Unknown topic '{topic}'", "check 'simple-ros2 topic list' for the exact name"), file=sys.stderr)
        return 1
    print(f"Type: {type_name}")
    print(f"Publisher count: {len(publishers)}")
    print(f"Subscription count: {len(subscribers)}")
    if verbose:
        for info in publishers:
            print(f"\n  Node name: {info.name}\n  Endpoint type: PUBLISHER")
        for info in subscribers:
            print(f"\n  Node name: {info.name}\n  Endpoint type: SUBSCRIPTION")
    return 0


def _echo(rest: list) -> int:
    if not rest:
        _usage()
        return 1
    topic = rest[0]
    topics = _collect_topics()
    if topic not in topics:
        print(ros_error(f"Unknown topic '{topic}'", "check 'simple-ros2 topic list' for the exact name; the publisher may not have started yet"), file=sys.stderr)
        return 1
    msg_type = resolve_type(topics[topic])

    with rclpy.init(args=[]):
        node = Node(ephemeral_node_name())
        node.create_subscription(msg_type, topic, lambda msg: print(format_yaml(msg) + "\n---"))
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
    return 0


def _pub(rest: list) -> int:
    parser = argparse.ArgumentParser(prog="simple-ros2 topic pub", add_help=False)
    parser.add_argument("topic")
    parser.add_argument("type")
    parser.add_argument("values", nargs="?", default="{}")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("-w", "--wait-matching-subscriptions", type=int, default=0)
    try:
        args = parser.parse_args(rest)
    except SystemExit:
        _usage()
        return 1

    msg_type = resolve_type(args.type)
    data = yaml.safe_load(args.values) or {}

    with rclpy.init(args=[]):
        node = Node(ephemeral_node_name())
        pub = node.create_publisher(msg_type, args.topic)

        if args.wait_matching_subscriptions:
            print(f"Waiting for at least {args.wait_matching_subscriptions} matching subscription(s)...")
            deadline = time.monotonic() + 5.0
            while len(node._peer_connections) < args.wait_matching_subscriptions and time.monotonic() < deadline:
                node._reactor.spin_once(timeout=0.1)

        msg = from_wire(msg_type, data)
        count = 0
        print("publisher: beginning loop")
        while True:
            count += 1
            pub.publish(msg)
            print(f"publishing #{count}: {msg}")
            if args.once:
                break
            node._reactor.spin_once(timeout=1.0 / args.rate)
        node.destroy_node()
    return 0
