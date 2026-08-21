"""rclpy.node.Node -- ties the registry (discovery) and transport (sockets)
together behind the real rclpy API surface.

Every publisher/subscription/service/client declared on a node updates the
node's registry entry and does an immediate one-shot discovery scan, not
just a wait for the periodic backstop poll -- see simple_ros_runtime for why
that matters for the tutorials' "topic echo starts immediately" feel.
"""

import atexit
import os
import time
import uuid as uuid_mod
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from rclpy import _context
from rclpy.executors import Future
from rclpy.impl.rcutils_logger import RcutilsLogger
from rclpy.parameter import Parameter
from simple_ros_runtime import registry
from simple_ros_runtime.errors import ros_error
from simple_ros_runtime.serialization import from_wire, to_wire
from simple_ros_runtime.transport import Reactor


def _type_name(cls: type) -> str:
    parts = cls.__module__.split(".")
    return "/".join(parts[-2:]) + "/" + cls.__name__


class Publisher:
    def __init__(self, node: "Node", msg_type: type, topic: str):
        self.node = node
        self.msg_type = msg_type
        self.topic = topic

    def publish(self, msg: Any) -> None:
        envelope = {
            "kind": "topic_msg",
            "channel": self.topic,
            "type": _type_name(self.msg_type),
            "data": to_wire(msg),
        }
        # Broadcast to every currently-connected peer; receivers filter by
        # channel against their own subscriptions, so this is correct even
        # though it's not the narrowest possible fan-out. Simplicity over
        # performance, per this project's stated priorities.
        for conn in list(self.node._peer_connections.values()):
            self.node._reactor.send(conn, envelope)


class Subscription:
    def __init__(self, node: "Node", msg_type: type, topic: str, callback: Callable):
        self.node = node
        self.msg_type = msg_type
        self.topic = topic
        self.callback = callback


class Service:
    def __init__(self, node: "Node", srv_type: type, name: str, callback: Callable):
        self.node = node
        self.srv_type = srv_type
        self.name = name
        self.callback = callback


class Client:
    def __init__(self, node: "Node", srv_type: type, name: str):
        self.node = node
        self.srv_type = srv_type
        self.name = name

    def wait_for_service(self, timeout_sec: Optional[float] = None) -> bool:
        deadline = None if timeout_sec is None else time.monotonic() + timeout_sec
        while self.node._connection_for_service(self.name) is None:
            self.node._reactor.spin_once(timeout=0.05)
            if deadline is not None and time.monotonic() >= deadline:
                return False
        return True

    def call_async(self, request: Any) -> Future:
        future = Future()
        conn = self.node._connection_for_service(self.name)
        if conn is None:
            # Real rclpy's tutorial pattern always calls wait_for_service()
            # first, so a genuinely-missing server here is not the common
            # path; leave the future pending rather than inventing behavior
            # no tutorial exercises.
            return future
        request_id = uuid_mod.uuid4().hex
        self.node._pending_service_calls[request_id] = future
        envelope = {
            "kind": "service_request",
            "channel": self.name,
            "type": _type_name(self.srv_type),
            "request_id": request_id,
            "data": to_wire(request),
        }
        self.node._reactor.send(conn, envelope)
        return future


class Node:
    def __init__(self, name: str, *, namespace: str = "/"):
        remaps = _context.remaps()
        self._name = remaps.get("__node", name)
        self._namespace = remaps.get("__ns", namespace)
        self._remaps = remaps
        self._uuid = uuid_mod.uuid4().hex
        self._shutdown_requested = False
        self._destroyed = False

        socket_path = registry.new_socket_path()
        self._reactor = Reactor(socket_path)
        self._reactor.on_envelope = self._handle_envelope
        self._socket_path = str(socket_path)

        self._publishers: dict[str, Publisher] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._services: dict[str, Service] = {}
        self._clients: dict[str, Client] = {}
        self._parameters: dict[str, Parameter] = {}

        self._peer_connections: dict[str, Any] = {}          # peer uuid -> Connection
        self._service_peer_uuid: dict[str, str] = {}          # service name -> peer uuid
        self._pending_service_calls: dict[str, Future] = {}   # request_id -> Future

        self._logger = RcutilsLogger(self._name)

        self._param_file_overrides = self._load_param_file_overrides()

        self._register_parameter_services()
        self._sync_registry()
        self._reactor.add_timer(0.5, self._discover_peers)

        atexit.register(self.destroy_node)

    # ---- basic accessors -------------------------------------------------

    def get_name(self) -> str:
        return self._name

    def get_logger(self) -> RcutilsLogger:
        return self._logger

    def get_namespace(self) -> str:
        return self._namespace

    # ---- graph entities ----------------------------------------------------

    def _remap(self, name: str) -> str:
        # Real ROS 2 resolves relative names to absolute (leading "/")
        # before matching against remap rules or putting them on the wire.
        if not name.startswith("/"):
            name = "/" + name
        return self._remaps.get(name, name)

    def create_publisher(self, msg_type: type, topic: str, qos_depth: int = 10) -> Publisher:
        topic = self._remap(topic)
        pub = Publisher(self, msg_type, topic)
        self._publishers[topic] = pub
        self._sync_registry()
        self._discover_peers()
        return pub

    def create_subscription(self, msg_type: type, topic: str, callback: Callable, qos_depth: int = 10) -> Subscription:
        topic = self._remap(topic)
        sub = Subscription(self, msg_type, topic, callback)
        self._subscriptions[topic] = sub
        self._sync_registry()
        self._discover_peers()
        return sub

    def create_service(self, srv_type: type, name: str, callback: Callable) -> Service:
        name = self._remap(name)
        srv = Service(self, srv_type, name, callback)
        self._services[name] = srv
        self._sync_registry()
        return srv

    def create_client(self, srv_type: type, name: str) -> Client:
        name = self._remap(name)
        cli = Client(self, srv_type, name)
        self._clients[name] = cli
        self._sync_registry()
        self._discover_peers()
        return cli

    def destroy_publisher(self, pub: Publisher) -> None:
        self._publishers.pop(pub.topic, None)
        self._sync_registry()

    def destroy_subscription(self, sub: Subscription) -> None:
        self._subscriptions.pop(sub.topic, None)
        self._sync_registry()

    def destroy_service(self, srv: Service) -> None:
        self._services.pop(srv.name, None)
        self._sync_registry()

    def create_timer(self, period_sec: float, callback: Callable):
        return self._reactor.add_timer(period_sec, callback)

    # ---- parameters ---------------------------------------------------------

    def declare_parameter(self, name: str, value: Any, descriptor: Any = None) -> Parameter:
        if name in self._param_file_overrides:
            value = self._param_file_overrides[name]
        param = Parameter(name, value=value)
        self._parameters[name] = param
        self._sync_registry()
        return param

    def get_parameter(self, name: str) -> Parameter:
        if name not in self._parameters:
            raise KeyError(
                ros_error(
                    f"Parameter '{name}' is not declared",
                    f"call declare_parameter('{name}', <default>) before get_parameter, or check the spelling",
                )
            )
        return self._parameters[name]

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters

    def set_parameters(self, parameters: list) -> list:
        results = []
        for param in parameters:
            if param.name in self._parameters:
                self._parameters[param.name] = param
                results.append(True)
            else:
                results.append(False)
        self._sync_registry()
        return results

    def _load_param_file_overrides(self) -> dict:
        params_file = _context.params_file()
        if not params_file:
            return {}
        with open(params_file) as f:
            data = yaml.safe_load(f) or {}
        node_section = data.get(self._name, {})
        return dict(node_section.get("ros__parameters", {}))

    def _register_parameter_services(self) -> None:
        from rcl_interfaces.msg import ParameterType, ParameterValue, SetParametersResult
        from rcl_interfaces.srv import GetParameters, SetParameters

        type_to_wire_type = {
            Parameter.Type.BOOL: ParameterType.PARAMETER_BOOL,
            Parameter.Type.INTEGER: ParameterType.PARAMETER_INTEGER,
            Parameter.Type.DOUBLE: ParameterType.PARAMETER_DOUBLE,
            Parameter.Type.STRING: ParameterType.PARAMETER_STRING,
            Parameter.Type.NOT_SET: ParameterType.PARAMETER_NOT_SET,
        }
        type_to_value_field = {
            Parameter.Type.BOOL: "bool_value",
            Parameter.Type.INTEGER: "integer_value",
            Parameter.Type.DOUBLE: "double_value",
            Parameter.Type.STRING: "string_value",
        }

        def _to_wire_value(param: Optional[Parameter]) -> ParameterValue:
            if param is None:
                return ParameterValue()
            pv = ParameterValue(type=type_to_wire_type[param.type_])
            field = type_to_value_field.get(param.type_)
            if field is not None:
                setattr(pv, field, param.value)
            return pv

        def _handle_get_parameters(request, response):
            response.values = [_to_wire_value(self._parameters.get(name)) for name in request.names]
            return response

        def _handle_set_parameters(request, response):
            for entry in request.parameters:
                current = self._parameters.get(entry.name)
                if current is None:
                    response.results.append(SetParametersResult(successful=False, reason=f"parameter '{entry.name}' not declared"))
                    continue
                field = type_to_value_field[current.type_]
                self._parameters[entry.name] = Parameter(entry.name, current.type_, getattr(entry.value, field))
                response.results.append(SetParametersResult(successful=True, reason=""))
            self._sync_registry()
            return response

        self.create_service(GetParameters, f"{self._name}/get_parameters", _handle_get_parameters)
        self.create_service(SetParameters, f"{self._name}/set_parameters", _handle_set_parameters)

    # ---- registry / discovery -------------------------------------------

    def _sync_registry(self) -> None:
        info = registry.NodeInfo(
            name=self._name,
            uuid=self._uuid,
            pid=os.getpid(),
            socket_path=self._socket_path,
            publications=[{"topic": t, "type": _type_name(p.msg_type)} for t, p in self._publishers.items()],
            subscriptions=[{"topic": t, "type": _type_name(s.msg_type)} for t, s in self._subscriptions.items()],
            services=[{"name": n, "type": _type_name(s.srv_type)} for n, s in self._services.items()],
            service_clients=[{"name": n, "type": _type_name(c.srv_type)} for n, c in self._clients.items()],
            parameters={n: p.value for n, p in self._parameters.items()},
        )
        registry.write_node_info(info)

    def _discover_peers(self) -> None:
        for peer in registry.scan_nodes():
            if peer.uuid == self._uuid:
                continue
            wants_connection = False
            for topic in self._publishers:
                if any(s["topic"] == topic for s in peer.subscriptions):
                    wants_connection = True
            for topic in self._subscriptions:
                if any(p["topic"] == topic for p in peer.publications):
                    wants_connection = True
            for name in self._clients:
                if any(s["name"] == name for s in peer.services):
                    wants_connection = True
                    self._service_peer_uuid[name] = peer.uuid
            if wants_connection and peer.uuid not in self._peer_connections:
                try:
                    conn = self._reactor.connect(peer.socket_path)
                except (ConnectionRefusedError, FileNotFoundError, OSError):
                    continue
                self._peer_connections[peer.uuid] = conn
                conn.on_close = self._on_peer_disconnect(peer.uuid)
                # Introduce ourselves so the accepting side can key this
                # same connection into its own _peer_connections too (see
                # the "hello" case in _handle_envelope) -- without this, a
                # node that's only ever connected *to* would never learn
                # which connection belongs to which peer, and
                # Publisher.publish() would have nothing to send over.
                self._reactor.send(conn, {"kind": "hello", "channel": "", "type": "", "data": {"uuid": self._uuid}})

    def _on_peer_disconnect(self, peer_uuid: str) -> Callable:
        def _handler(conn):
            self._peer_connections.pop(peer_uuid, None)

        return _handler

    def _connection_for_service(self, name: str):
        peer_uuid = self._service_peer_uuid.get(name)
        if peer_uuid is None or peer_uuid not in self._peer_connections:
            self._discover_peers()
            peer_uuid = self._service_peer_uuid.get(name)
        return self._peer_connections.get(peer_uuid) if peer_uuid else None

    # ---- envelope dispatch -------------------------------------------------

    def _handle_envelope(self, envelope: dict, conn) -> None:
        kind = envelope["kind"]
        channel = envelope["channel"]
        if kind == "hello":
            peer_uuid = envelope["data"]["uuid"]
            self._peer_connections[peer_uuid] = conn
            conn.on_close = self._on_peer_disconnect(peer_uuid)
        elif kind == "topic_msg":
            sub = self._subscriptions.get(channel)
            if sub is not None:
                sub.callback(from_wire(sub.msg_type, envelope["data"]))
        elif kind == "service_request":
            srv = self._services.get(channel)
            if srv is None:
                return
            request = from_wire(srv.srv_type.Request, envelope["data"])
            response = srv.srv_type.Response()
            result = srv.callback(request, response)
            if result is not None:
                response = result
            self._reactor.send(
                conn,
                {
                    "kind": "service_response",
                    "channel": channel,
                    "type": _type_name(srv.srv_type),
                    "request_id": envelope["request_id"],
                    "data": to_wire(response),
                },
            )
        elif kind == "service_response":
            future = self._pending_service_calls.pop(envelope["request_id"], None)
            cli = self._clients.get(channel)
            if future is not None and cli is not None:
                future.set_result(from_wire(cli.srv_type.Response, envelope["data"]))

    # ---- lifecycle ----------------------------------------------------------

    def destroy_node(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        info = registry.NodeInfo(
            name=self._name,
            uuid=self._uuid,
            pid=os.getpid(),
            socket_path=self._socket_path,
            publications=[],
            subscriptions=[],
            services=[],
            service_clients=[],
            parameters={},
        )
        registry.remove_node_info(info)
        self._reactor.close()
