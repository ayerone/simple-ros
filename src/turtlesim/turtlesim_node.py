"""turtlesim_node: a tkinter-windowed simulator, matching real turtlesim's
topics/services/parameters (see CLAUDE.md's turtlesim spec section for the
exact surface this implements).
"""

import math
import tkinter as tk
from typing import Callable, Dict, Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_srvs.srv import Empty
from turtlesim_msgs.msg import Color, Pose
from turtlesim_msgs.srv import Kill, SetPen, Spawn, TeleportAbsolute, TeleportRelative

WORLD_SIZE = 11.0
SCALE = 45
WINDOW_SIZE = round(WORLD_SIZE * SCALE)
DEFAULT_PEN = (0xB2, 0x17, 0x17)


class _Turtle:
    def __init__(self, name: str, x: float, y: float, theta: float):
        self.name = name
        self.x = x
        self.y = y
        self.theta = theta
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.pen_r, self.pen_g, self.pen_b = DEFAULT_PEN
        self.pen_width = 3
        self.pen_off = False
        self.canvas_item: Optional[int] = None
        self.pose_pub = None
        self.color_pub = None
        self.cmd_vel_sub = None
        self.set_pen_srv = None
        self.teleport_abs_srv = None
        self.teleport_rel_srv = None


class TurtlesimNode(Node):
    def __init__(self):
        super().__init__("turtlesim")

        self.declare_parameter("background_r", 69)
        self.declare_parameter("background_g", 86)
        self.declare_parameter("background_b", 255)

        self._turtles: Dict[str, _Turtle] = {}
        self._next_turtle_number = 2

        self._root = tk.Tk()
        self._root.title("TurtleSim")
        self._canvas = tk.Canvas(self._root, width=WINDOW_SIZE, height=WINDOW_SIZE, highlightthickness=0)
        self._canvas.pack()

        self.create_service(Empty, "/clear", self._handle_clear)
        self.create_service(Empty, "/reset", self._handle_reset)
        self.create_service(Spawn, "/spawn", self._handle_spawn)
        self.create_service(Kill, "/kill", self._handle_kill)

        self._spawn_turtle("turtle1", WORLD_SIZE / 2, WORLD_SIZE / 2, 0.0)

        self.create_timer(1 / 60, self._simulation_step)
        self.create_timer(1 / 30, self._render)

    # ---- world <-> canvas coordinates --------------------------------------

    def _to_canvas(self, x: float, y: float) -> tuple:
        return x * SCALE, WINDOW_SIZE - y * SCALE

    def _turtle_points(self, turtle: _Turtle) -> list:
        cx, cy = self._to_canvas(turtle.x, turtle.y)
        size = SCALE * 0.5
        theta = turtle.theta
        nose = (cx + size * math.cos(theta), cy - size * math.sin(theta))
        back_left = (cx + size * 0.6 * math.cos(theta + 2.6), cy - size * 0.6 * math.sin(theta + 2.6))
        back_right = (cx + size * 0.6 * math.cos(theta - 2.6), cy - size * 0.6 * math.sin(theta - 2.6))
        return [*nose, *back_left, *back_right]

    # ---- turtle lifecycle ---------------------------------------------------

    def _generate_turtle_name(self) -> str:
        name = f"turtle{self._next_turtle_number}"
        self._next_turtle_number += 1
        return name

    def _spawn_turtle(self, name: str, x: float, y: float, theta: float) -> None:
        turtle = _Turtle(name, x, y, theta)
        self._turtles[name] = turtle
        turtle.pose_pub = self.create_publisher(Pose, f"{name}/pose")
        turtle.color_pub = self.create_publisher(Color, f"{name}/color_sensor")
        turtle.cmd_vel_sub = self.create_subscription(Twist, f"{name}/cmd_vel", self._cmd_vel_handler(name))
        turtle.set_pen_srv = self.create_service(SetPen, f"{name}/set_pen", self._set_pen_handler(name))
        turtle.teleport_abs_srv = self.create_service(TeleportAbsolute, f"{name}/teleport_absolute", self._teleport_absolute_handler(name))
        turtle.teleport_rel_srv = self.create_service(TeleportRelative, f"{name}/teleport_relative", self._teleport_relative_handler(name))
        turtle.canvas_item = self._canvas.create_polygon(*self._turtle_points(turtle), fill="#%02x%02x%02x" % (turtle.pen_r, turtle.pen_g, turtle.pen_b))
        self.get_logger().info(f"Spawning turtle [{name}] at x=[{x:.6f}], y=[{y:.6f}], theta=[{theta:.6f}]")

    def _kill_turtle(self, name: str) -> None:
        turtle = self._turtles.pop(name)
        self.destroy_publisher(turtle.pose_pub)
        self.destroy_publisher(turtle.color_pub)
        self.destroy_subscription(turtle.cmd_vel_sub)
        self.destroy_service(turtle.set_pen_srv)
        self.destroy_service(turtle.teleport_abs_srv)
        self.destroy_service(turtle.teleport_rel_srv)
        self._canvas.delete(turtle.canvas_item)

    # ---- services -------------------------------------------------------------

    def _handle_clear(self, request, response):
        self._canvas.delete("trail")
        return response

    def _handle_reset(self, request, response):
        for name in list(self._turtles):
            self._kill_turtle(name)
        self._canvas.delete("trail")
        self._next_turtle_number = 2
        self._spawn_turtle("turtle1", WORLD_SIZE / 2, WORLD_SIZE / 2, 0.0)
        return response

    def _handle_spawn(self, request, response):
        name = request.name or self._generate_turtle_name()
        if name in self._turtles:
            self.get_logger().error(f"A turtle named [{name}] already exists")
            response.name = ""
            return response
        self._spawn_turtle(name, request.x, request.y, request.theta)
        response.name = name
        return response

    def _handle_kill(self, request, response):
        if request.name in self._turtles:
            self._kill_turtle(request.name)
        return response

    def _set_pen_handler(self, name: str) -> Callable:
        def handler(request, response):
            turtle = self._turtles[name]
            turtle.pen_r, turtle.pen_g, turtle.pen_b = request.r, request.g, request.b
            turtle.pen_width = request.width
            turtle.pen_off = bool(request.off)
            return response

        return handler

    def _teleport_absolute_handler(self, name: str) -> Callable:
        def handler(request, response):
            turtle = self._turtles[name]
            turtle.x, turtle.y, turtle.theta = request.x, request.y, request.theta
            return response

        return handler

    def _teleport_relative_handler(self, name: str) -> Callable:
        def handler(request, response):
            turtle = self._turtles[name]
            turtle.theta += request.angular
            turtle.x += request.linear * math.cos(turtle.theta)
            turtle.y += request.linear * math.sin(turtle.theta)
            return response

        return handler

    def _cmd_vel_handler(self, name: str) -> Callable:
        def handler(msg: Twist):
            turtle = self._turtles[name]
            turtle.linear_velocity = msg.linear.x
            turtle.angular_velocity = msg.angular.z

        return handler

    # ---- simulation + rendering --------------------------------------------

    def _simulation_step(self) -> None:
        dt = 1 / 60
        for turtle in self._turtles.values():
            if turtle.linear_velocity == 0.0 and turtle.angular_velocity == 0.0:
                continue
            new_x = turtle.x + turtle.linear_velocity * math.cos(turtle.theta) * dt
            new_y = turtle.y + turtle.linear_velocity * math.sin(turtle.theta) * dt
            new_x = max(0.0, min(WORLD_SIZE, new_x))
            new_y = max(0.0, min(WORLD_SIZE, new_y))
            if not turtle.pen_off and (new_x != turtle.x or new_y != turtle.y):
                x1, y1 = self._to_canvas(turtle.x, turtle.y)
                x2, y2 = self._to_canvas(new_x, new_y)
                self._canvas.create_line(x1, y1, x2, y2, fill="#%02x%02x%02x" % (turtle.pen_r, turtle.pen_g, turtle.pen_b), width=turtle.pen_width, tags="trail")
            turtle.x, turtle.y = new_x, new_y
            turtle.theta += turtle.angular_velocity * dt

        for turtle in self._turtles.values():
            turtle.pose_pub.publish(Pose(x=turtle.x, y=turtle.y, theta=turtle.theta, linear_velocity=turtle.linear_velocity, angular_velocity=turtle.angular_velocity))
            bg_r = self.get_parameter("background_r").value
            bg_g = self.get_parameter("background_g").value
            bg_b = self.get_parameter("background_b").value
            turtle.color_pub.publish(Color(r=bg_r, g=bg_g, b=bg_b))

    def _render(self) -> None:
        bg_r = self.get_parameter("background_r").value
        bg_g = self.get_parameter("background_g").value
        bg_b = self.get_parameter("background_b").value
        self._canvas.configure(bg="#%02x%02x%02x" % (bg_r, bg_g, bg_b))
        for turtle in self._turtles.values():
            self._canvas.coords(turtle.canvas_item, *self._turtle_points(turtle))
            self._canvas.itemconfigure(turtle.canvas_item, fill="#%02x%02x%02x" % (turtle.pen_r, turtle.pen_g, turtle.pen_b))
        try:
            self._root.update()
        except tk.TclError:
            self._shutdown_requested = True


def main(args=None):
    try:
        with rclpy.init(args=args):
            node = TurtlesimNode()
            rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass


if __name__ == "__main__":
    main()
