import os
import subprocess
import sys

import pytest

from simple_ros_runtime import registry


@pytest.fixture(autouse=True)
def isolated_registry(tmp_path, monkeypatch):
    # sys.prefix drives registry_dir(); point it at a tmp dir per test so
    # tests don't collide with each other or with a real running node.
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    yield


def make_node_info(name="talker", pid=None):
    return registry.NodeInfo(
        name=name,
        uuid="abc123",
        pid=pid if pid is not None else os.getpid(),
        socket_path=str(registry.sockets_dir() / "abc123.sock"),
        publications=[{"topic": "/chatter", "type": "std_msgs/msg/String"}],
        subscriptions=[],
        services=[],
        service_clients=[],
        parameters={},
    )


def test_write_and_scan_roundtrip():
    info = make_node_info()
    registry.write_node_info(info)
    found = registry.scan_nodes()
    assert len(found) == 1
    assert found[0] == info


def test_scan_prunes_dead_pid():
    # A pid that's certainly not alive: spawn a process and wait for it to exit.
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    dead_pid = proc.pid
    info = make_node_info(pid=dead_pid)
    registry.write_node_info(info)
    assert info.registry_path().exists()

    found = registry.scan_nodes()

    assert found == []
    assert not info.registry_path().exists()


def test_write_is_atomic_no_tmp_file_left_behind():
    info = make_node_info()
    registry.write_node_info(info)
    leftovers = list(registry.registry_dir().glob("*.tmp-*"))
    assert leftovers == []


def test_remove_node_info_cleans_up_both_files():
    info = make_node_info()
    registry.write_node_info(info)
    open(info.socket_path, "w").close()  # stand in for a real bound socket
    registry.remove_node_info(info)
    assert not info.registry_path().exists()
    assert not os.path.exists(info.socket_path)
