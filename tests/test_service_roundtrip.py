import sys
import threading

import pytest

from example_interfaces.srv import AddTwoInts
from rclpy.executors import spin_until_future_complete
from rclpy.node import Node


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    yield


def _pump(*nodes, rounds=30, delay=0.02):
    for _ in range(rounds):
        for node in nodes:
            node._reactor.spin_once(timeout=delay)


def _spin_in_background(node) -> threading.Event:
    """Real deployment is two separate processes, each independently
    spinning; spin_until_future_complete on the client side only spins the
    client's own reactor, which is correct there but means an in-process
    test needs something actually running the server's loop too."""
    stop = threading.Event()
    thread = threading.Thread(target=lambda: node._reactor.spin(should_continue=lambda: not stop.is_set()), daemon=True)
    thread.start()
    return stop


def test_service_call_async_roundtrip():
    server_node = Node("minimal_service")

    def add_two_ints_callback(request, response):
        response.sum = request.a + request.b
        return response

    server_node.create_service(AddTwoInts, "add_two_ints", add_two_ints_callback)
    stop_server = _spin_in_background(server_node)

    client_node = Node("minimal_client_async")
    client = client_node.create_client(AddTwoInts, "add_two_ints")

    assert client.wait_for_service(timeout_sec=2.0)

    request = AddTwoInts.Request()
    request.a = 41
    request.b = 1
    future = client.call_async(request)
    spin_until_future_complete(client_node, future, timeout_sec=2.0)

    assert future.done()
    assert future.result().sum == 42

    stop_server.set()
    server_node.destroy_node()
    client_node.destroy_node()


def test_multiple_in_flight_requests_are_correlated_by_request_id():
    server_node = Node("adder")

    def add_two_ints_callback(request, response):
        response.sum = request.a + request.b
        return response

    server_node.create_service(AddTwoInts, "add_two_ints", add_two_ints_callback)

    client_node = Node("caller")
    client = client_node.create_client(AddTwoInts, "add_two_ints")
    assert client.wait_for_service(timeout_sec=2.0)

    request_a = AddTwoInts.Request(a=1, b=1)
    request_b = AddTwoInts.Request(a=100, b=200)
    future_a = client.call_async(request_a)
    future_b = client.call_async(request_b)

    for _ in range(30):
        client_node._reactor.spin_once(timeout=0.02)
        server_node._reactor.spin_once(timeout=0.02)
        if future_a.done() and future_b.done():
            break

    assert future_a.result().sum == 2
    assert future_b.result().sum == 300

    server_node.destroy_node()
    client_node.destroy_node()


def test_parameter_get_and_set_services():
    from rcl_interfaces.msg import ParameterType
    from rcl_interfaces.srv import GetParameters, SetParameters

    param_node = Node("turtlesim")
    param_node.declare_parameter("background_r", 69)
    stop_param_node = _spin_in_background(param_node)

    client_node = Node("param_client")
    get_client = client_node.create_client(GetParameters, "turtlesim/get_parameters")
    set_client = client_node.create_client(SetParameters, "turtlesim/set_parameters")
    assert get_client.wait_for_service(timeout_sec=2.0)
    assert set_client.wait_for_service(timeout_sec=2.0)

    get_future = get_client.call_async(GetParameters.Request(names=["background_r"]))
    spin_until_future_complete(client_node, get_future, timeout_sec=2.0)
    value = get_future.result().values[0]
    assert value.type == ParameterType.PARAMETER_INTEGER
    assert value.integer_value == 69

    from rcl_interfaces.msg import Parameter as WireParameter
    from rcl_interfaces.msg import ParameterValue

    set_request = SetParameters.Request(
        parameters=[WireParameter(name="background_r", value=ParameterValue(type=ParameterType.PARAMETER_INTEGER, integer_value=150))]
    )
    set_future = set_client.call_async(set_request)
    spin_until_future_complete(client_node, set_future, timeout_sec=2.0)
    assert set_future.result().results[0].successful

    assert param_node.get_parameter("background_r").value == 150

    stop_param_node.set()
    param_node.destroy_node()
    client_node.destroy_node()
