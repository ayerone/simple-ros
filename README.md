# simple-ros

A pure-Python stand-in for basic features of ROS 2, for learning the official Beginner tutorials without installing full ROS 2. Based on ROS2 **Lyrical**.

**Docs/Tutorials: [ayerone.github.io/simple-ros](https://ayerone.github.io/simple-ros/)**

## Quick start

```console
$ git clone https://github.com/ayerone/simple-ros.git
$ cd simple-ros
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
```

<details>
<summary id="basic-python-setup">Basic Python setup</summary>

If your system doesn't already have Python's venv module/pip:

```console
# For debian-based Linux, such as Ubuntu:
$ sudo apt update
$ sudo apt install python3-venv python3-pip
```
</details>

See the [docs site](https://ayerone.github.io/simple-ros/) for the full installation guide and tutorials.

## What this is

simple-ros reimplements enough of ROS 2 (nodes, topics, services, actions, parameters, and the `rclpy` API) to work through the tutorials without having to install any system packages. Node names, topic names, message/service shapes, and the `rclpy` API are identical to real ROS 2; only the outer command-line tools are renamed (`ros2` becomes `simple-ros2`, and so on).
**Note:** This project is a work in progress, and not all features/tutorials are implemented or correct yet.
See [About simple-ros](https://ayerone.github.io/simple-ros/About-simple-ros.html) and [Development Status](https://ayerone.github.io/simple-ros/Development-Status.html) for what's implemented so far.

This project is not affiliated with Open Robotics or the ROS 2 project.
