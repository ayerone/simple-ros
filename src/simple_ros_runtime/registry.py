"""Filesystem-based node registry: no daemon, just shared storage.

Each running node writes one JSON file describing itself (name, uuid, pid,
socket path, and what it publishes/subscribes/serves) into a directory
scoped to the active venv. Any node or CLI tool that wants to find peers
scans this directory directly; there is no process relaying anything.

Registry files live under ``sys.prefix`` (the active venv), so deleting the
venv deletes the registry too. Socket files live somewhere short instead
(``$XDG_RUNTIME_DIR`` or ``/tmp``), since AF_UNIX socket paths are capped at
108 bytes on Linux and a venv path can easily exceed that once combined with
a node name and uuid.
"""

import dataclasses
import json
import os
import sys
import uuid
from pathlib import Path


def domain_id() -> str:
    return os.environ.get("SIMPLE_ROS_DOMAIN_ID", "0")


def registry_dir() -> Path:
    path = Path(sys.prefix) / "var" / "simple_ros" / "domains" / domain_id() / "nodes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sockets_dir() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and Path(runtime_dir).is_dir():
        path = Path(runtime_dir) / "simple_ros"
    else:
        path = Path("/tmp") / f"simple_ros-{os.getuid()}"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def new_socket_path() -> Path:
    return sockets_dir() / f"{uuid.uuid4().hex}.sock"


@dataclasses.dataclass
class NodeInfo:
    name: str
    uuid: str
    pid: int
    socket_path: str
    publications: list       # [{"topic": str, "type": str}]
    subscriptions: list      # [{"topic": str, "type": str}]
    services: list           # [{"name": str, "type": str}]
    service_clients: list    # [{"name": str, "type": str}]
    parameters: dict         # {name: value}

    def registry_path(self) -> Path:
        return registry_dir() / f"{self.name}-{self.uuid}.json"


def write_node_info(info: NodeInfo) -> None:
    """Write atomically: tmp file + os.replace(), never a direct write.

    A scanner may be reading this same directory concurrently; a torn write
    would hand it invalid JSON.
    """
    path = info.registry_path()
    tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp_path.write_text(json.dumps(dataclasses.asdict(info)))
    os.replace(tmp_path, path)


def remove_node_info(info: NodeInfo) -> None:
    for path in (info.registry_path(), Path(info.socket_path)):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def scan_nodes() -> list[NodeInfo]:
    """Return all live node registrations, pruning stale ones as found.

    A node that died without cleaning up after itself (SIGKILL, crash) is
    detected by checking whether its recorded pid is still alive, not by
    any cleanup the dead process itself could have run. Whichever scanner
    notices a stale entry unlinks both its JSON file and its socket file,
    so cleanup is self-healing with no daemon involved.
    """
    nodes = []
    for path in registry_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            continue
        if not _pid_alive(data["pid"]):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            try:
                Path(data["socket_path"]).unlink()
            except FileNotFoundError:
                pass
            continue
        nodes.append(NodeInfo(**data))
    return nodes
