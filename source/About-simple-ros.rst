.. _AboutSimpleRos:

About ROS 2 and simple-ros
============================

.. container:: simple-ros-banner

   This is simple-ros, not the official `ROS 2 project <https://docs.ros.org/en/lyrical/>`__.

About ROS
---------

ROS (Robot Operating System) is an open-source ecosystem that provides the framework, tools, and libraries for building, deploying, running, and maintaining robotic applications. If you want to know more, see the `official ROS documentation <https://docs.ros.org/en/lyrical/About-ROS.html>`__.

About simple-ros
------------------

simple-ros exists to remove the [somewhat complicated] installation step from learning ROS 2 basics. ``pip install`` in a virtual environment gives you a working stand-in for a full ROS 2 installation, so you can start learning with the tutorials instantly.

What it is
^^^^^^^^^^^^

A from-scratch, pure-Python reimplementation of just enough of ROS 2 (nodes, topics, services, actions, parameters, and the ``rclpy`` API) to work through the official Beginner tutorials with no daemon, no DDS, and no system packages underneath. Node names, topic names, message and service shapes, and every ``rclpy`` call you write are identical to real ROS 2; the only things renamed are the outer command-line tools (``ros2`` becomes ``simple-ros2``, and so on).

Based on ROS2 **Lyrical**.

The tutorial pages on this site are the same tutorials published by the real ROS 2 project, run against simple-ros instead of a real, full ROS 2 install.

What it is not
^^^^^^^^^^^^^^^^

Not a competing framework, and not aiming for performance, realism, or feature completeness beyond what the tutorials need.
