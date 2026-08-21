import sys

import pytest

from geometry_msgs.msg import Twist, Vector3
from rclpy.node import Node
from std_msgs.msg import String


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    yield


def _pump(*nodes, rounds=30, delay=0.02):
    for _ in range(rounds):
        for node in nodes:
            node._reactor.spin_once(timeout=delay)


def test_publisher_subscriber_roundtrip():
    publisher_node = Node("talker")
    pub = publisher_node.create_publisher(String, "/chatter")

    received = []
    subscriber_node = Node("listener")
    subscriber_node.create_subscription(String, "/chatter", lambda msg: received.append(msg))

    _pump(publisher_node, subscriber_node)  # let the hello handshake settle

    pub.publish(String(data="hello"))
    _pump(publisher_node, subscriber_node)

    assert len(received) == 1
    assert received[0].data == "hello"

    publisher_node.destroy_node()
    subscriber_node.destroy_node()


def test_nested_message_roundtrip_over_real_transport():
    # Twist is exactly the type that broke under a naive from_wire.
    publisher_node = Node("teleop_turtle")
    pub = publisher_node.create_publisher(Twist, "/turtle1/cmd_vel")

    received = []
    subscriber_node = Node("turtlesim")
    subscriber_node.create_subscription(Twist, "/turtle1/cmd_vel", lambda msg: received.append(msg))

    _pump(publisher_node, subscriber_node)

    pub.publish(Twist(linear=Vector3(x=2.0), angular=Vector3(z=1.8)))
    _pump(publisher_node, subscriber_node)

    assert len(received) == 1
    assert isinstance(received[0].linear, Vector3)
    assert received[0].linear.x == 2.0
    assert received[0].angular.z == 1.8

    publisher_node.destroy_node()
    subscriber_node.destroy_node()


def test_publisher_created_before_subscriber_still_connects():
    # Mirrors the real tutorial ordering: turtlesim (publisher of /pose) is
    # already running before a learner runs `topic echo`. Whichever side is
    # created *later* must discover the earlier one immediately.
    publisher_node = Node("early_publisher")
    pub = publisher_node.create_publisher(String, "/topic")
    _pump(publisher_node)

    received = []
    subscriber_node = Node("late_subscriber")
    subscriber_node.create_subscription(String, "/topic", lambda msg: received.append(msg))
    _pump(publisher_node, subscriber_node)

    pub.publish(String(data="already running"))
    _pump(publisher_node, subscriber_node)

    assert len(received) == 1
    assert received[0].data == "already running"

    publisher_node.destroy_node()
    subscriber_node.destroy_node()
