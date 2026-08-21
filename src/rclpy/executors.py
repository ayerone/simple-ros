"""Spinning a Node: a thin wrapper over its Reactor's selectors loop.

Single-threaded by design -- nothing in the tutorials this project targets
uses a MultiThreadedExecutor or callback groups, and single-threaded spin
matches real rclpy's default callback-serialization behavior anyway (one
callback at a time, in readiness order).
"""

from typing import Any, Callable


class ExternalShutdownException(Exception):
    """Raised on shutdown so `except (KeyboardInterrupt, ExternalShutdownException)`
    (the pattern every copied tutorial's main() uses) has something real to catch."""


class Future:
    def __init__(self):
        self._done = False
        self._result: Any = None
        self._exception: Exception | None = None

    def done(self) -> bool:
        return self._done

    def result(self) -> Any:
        if self._exception is not None:
            raise self._exception
        return self._result

    def set_result(self, value: Any) -> None:
        self._result = value
        self._done = True

    def set_exception(self, exc: Exception) -> None:
        self._exception = exc
        self._done = True


def spin(node: "rclpy.node.Node") -> None:  # noqa: F821 -- avoid a circular import at module load time
    node._reactor.spin(should_continue=lambda: not node._shutdown_requested)


def spin_once(node: "rclpy.node.Node", timeout_sec: float | None = None) -> None:  # noqa: F821
    node._reactor.spin_once(timeout=timeout_sec)


def spin_until_future_complete(node: "rclpy.node.Node", future: Future, timeout_sec: float | None = None) -> None:  # noqa: F821
    import time

    deadline = None if timeout_sec is None else time.monotonic() + timeout_sec
    while not future.done() and not node._shutdown_requested:
        remaining = None
        if deadline is not None:
            remaining = max(0.0, deadline - time.monotonic())
            if remaining <= 0:
                return
        node._reactor.spin_once(timeout=remaining)
