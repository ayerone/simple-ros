"""turtle_teleop_key: reads arrow keys without requiring Enter and publishes
Twist to turtle1/cmd_vel. Rotation keys (G|B|V|C|D|E|R|T|F) are a deliberate
no-op stub for this milestone -- action support (which those keys drive in
real turtlesim) lands in a follow-up milestone, see CLAUDE.md.
"""

import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist, Vector3
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

BANNER = "Use arrow keys to move the turtle.\nUse G|B|V|C|D|E|R|T keys to rotate to absolute orientations. 'F' to cancel a rotation.\n"

_MOVE_BINDINGS = {
    "\x1b[A": (1, 0),  # up: forward
    "\x1b[B": (-1, 0),  # down: backward
    "\x1b[D": (0, 1),  # left: rotate ccw
    "\x1b[C": (0, -1),  # right: rotate cw
}


class TeleopKeyNode(Node):
    def __init__(self):
        super().__init__("teleop_turtle")
        self.declare_parameter("scale_linear", 2.0)
        self.declare_parameter("scale_angular", 2.0)
        self._pub = self.create_publisher(Twist, "turtle1/cmd_vel", 10)

    def publish_twist(self, linear: float, angular: float) -> None:
        scale_linear = self.get_parameter("scale_linear").value
        scale_angular = self.get_parameter("scale_angular").value
        self._pub.publish(Twist(linear=Vector3(x=linear * scale_linear), angular=Vector3(z=angular * scale_angular)))


def _read_key() -> str:
    if not select.select([sys.stdin], [], [], 0.1)[0]:
        return ""
    key = sys.stdin.read(1)
    if key == "\x1b":
        key += sys.stdin.read(2)
    return key


def main(args=None):
    try:
        with rclpy.init(args=args):
            node = TeleopKeyNode()
            print(BANNER)
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    node._reactor.spin_once(timeout=0.0)
                    key = _read_key()
                    if key in _MOVE_BINDINGS:
                        linear, angular = _MOVE_BINDINGS[key]
                        node.publish_twist(linear, angular)
                    elif key in ("q", "\x03"):
                        break
                    # G|B|V|C|D|E|R|T|F: no-op in this milestone, see module docstring.
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass


if __name__ == "__main__":
    main()
