# simple-ros

A pure-Python stand-in for ROS 2, for learning the official Beginner tutorials without installing real ROS 2.

**Docs: [ayerone.github.io/simple-ros](https://ayerone.github.io/simple-ros/)**

## Quick start

```console
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
$ simple-ros2 doctor
```

See the [docs site](https://ayerone.github.io/simple-ros/) for the full installation guide and tutorials.

## What this is

simple-ros reimplements enough of ROS 2 (nodes, topics, services, actions, parameters, and the `rclpy` API) to work through the tutorials with no daemon, no DDS, and no system packages underneath. Node names, topic names, message/service shapes, and the `rclpy` API are identical to real ROS 2; only the outer command-line tools are renamed (`ros2` becomes `simple-ros2`, and so on). See [About simple-ros](https://ayerone.github.io/simple-ros/About-simple-ros.html) for the full explanation and [Development Status](https://ayerone.github.io/simple-ros/Development-Status.html) for what's actually implemented today.

This project is not affiliated with Open Robotics or the ROS 2 project.
