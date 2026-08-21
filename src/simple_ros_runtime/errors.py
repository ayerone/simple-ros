"""Error message convention: mirror real ROS 2's wording, then add a tip.

Every error a learner can hit should read as the real ROS 2 message first
(verified against real ros2cli/rclpy source or the tutorial text, not
invented), followed by a simple-ros-specific line explaining what actually
went wrong here and how to fix it. Real ROS 2's own text is often terse or
references concepts (daemons, RMW, discovery) that don't exist in this
system; the tip is where that gets translated into something actionable.
"""


def ros_error(real_message: str, tip: str) -> str:
    return f"{real_message}\nsimple-ros: {tip}"
