"""rclpy -- the simple-ros client library, matching real rclpy's user-facing
API (module functions, Node, Parameter, executors) with an independent
pure-Python implementation underneath. See CLAUDE.md for the full picture.
"""

import sys as _sys
from typing import Optional

from rclpy import _context
from rclpy import executors  # noqa: F401 -- exposes rclpy.executors.*
from rclpy import parameter  # noqa: F401 -- exposes rclpy.parameter.*
from rclpy.executors import Future
from rclpy.parameter import Parameter  # noqa: F401 -- exposes rclpy.Parameter


class _InitContext:
    def __enter__(self) -> "_InitContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False


def init(args: Optional[list] = None) -> _InitContext:
    argv = args if args is not None else _sys.argv[1:]
    _context.set_from_args(argv)
    return _InitContext()


def shutdown() -> None:
    _context.reset()


def spin(node) -> None:
    executors.spin(node)


def spin_once(node, timeout_sec: Optional[float] = None) -> None:
    executors.spin_once(node, timeout_sec)


def spin_until_future_complete(node, future: Future, timeout_sec: Optional[float] = None) -> None:
    executors.spin_until_future_complete(node, future, timeout_sec)
