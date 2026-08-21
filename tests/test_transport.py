import json
import socket

import pytest

from simple_ros_runtime.transport import Reactor


@pytest.fixture
def reactor(tmp_path):
    r = Reactor(tmp_path / "server.sock")
    yield r
    r.close()


def test_connect_send_receive_envelope(reactor, tmp_path):
    received = []
    reactor.on_envelope = lambda envelope, conn: received.append(envelope)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(tmp_path / "server.sock"))
    client_sock.sendall(json.dumps({"kind": "topic_msg", "channel": "/chatter", "type": "std_msgs/msg/String", "data": {"data": "hi"}}).encode() + b"\n")

    for _ in range(20):
        reactor.spin_once(timeout=0.1)
        if received:
            break

    assert received == [{"kind": "topic_msg", "channel": "/chatter", "type": "std_msgs/msg/String", "data": {"data": "hi"}}]
    client_sock.close()


def test_reactor_send_reaches_peer(reactor, tmp_path):
    accepted = []
    reactor.on_accept = lambda conn: accepted.append(conn)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(tmp_path / "server.sock"))

    for _ in range(20):
        reactor.spin_once(timeout=0.1)
        if accepted:
            break
    assert accepted

    reactor.send(accepted[0], {"kind": "topic_msg", "channel": "/pose", "type": "turtlesim_msgs/msg/Pose", "data": {"x": 1.0}})

    client_sock.settimeout(2.0)
    line = client_sock.makefile("rb").readline()
    assert json.loads(line) == {"kind": "topic_msg", "channel": "/pose", "type": "turtlesim_msgs/msg/Pose", "data": {"x": 1.0}}
    client_sock.close()


def test_line_split_across_two_writes_is_still_parsed_as_one_envelope(reactor, tmp_path):
    # recv() gives no message-boundary guarantees: force a single JSON line
    # across two separate socket writes and confirm it's still parsed whole.
    received = []
    reactor.on_envelope = lambda envelope, conn: received.append(envelope)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(tmp_path / "server.sock"))

    payload = json.dumps({"kind": "topic_msg", "channel": "/chatter", "type": "std_msgs/msg/String", "data": {"data": "split me"}}).encode() + b"\n"
    midpoint = len(payload) // 2
    client_sock.sendall(payload[:midpoint])
    reactor.spin_once(timeout=0.1)
    assert received == []  # first half alone must not be mistaken for a complete envelope

    client_sock.sendall(payload[midpoint:])
    for _ in range(20):
        reactor.spin_once(timeout=0.1)
        if received:
            break

    assert received == [{"kind": "topic_msg", "channel": "/chatter", "type": "std_msgs/msg/String", "data": {"data": "split me"}}]
    client_sock.close()


def test_multiple_envelopes_in_one_chunk_are_all_parsed(reactor, tmp_path):
    received = []
    reactor.on_envelope = lambda envelope, conn: received.append(envelope)

    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(str(tmp_path / "server.sock"))

    burst = b"".join(
        json.dumps({"kind": "topic_msg", "channel": "/pose", "type": "turtlesim_msgs/msg/Pose", "data": {"x": float(i)}}).encode() + b"\n"
        for i in range(5)
    )
    client_sock.sendall(burst)

    for _ in range(20):
        reactor.spin_once(timeout=0.1)
        if len(received) == 5:
            break

    assert [envelope["data"]["x"] for envelope in received] == [0.0, 1.0, 2.0, 3.0, 4.0]
    client_sock.close()
