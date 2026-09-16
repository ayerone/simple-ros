.. _AboutSimpleRos:

About simple-ros
================

simple-ros exists to remove the installation step from learning ROS 2. The official Beginner tutorials are excellent, but working through them for real means picking a Tier 1 platform, matching an Ubuntu LTS to a specific ROS 2 distro, and getting a DDS implementation running before you've touched a single line of robotics code. simple-ros skips all of that: ``pip install`` in a virtual environment gives you a working stand-in for a full ROS 2 underlay, so you can start the tutorials in minutes.

**Area: ROS-framework | Content-type: overview | Experience: beginner**

What it is
------------

A from-scratch, pure-Python reimplementation of just enough of ROS 2 (nodes, topics, services, actions, parameters, and the ``rclpy`` API) to work through the official Beginner tutorials with no daemon, no DDS, and no system packages underneath. Node names, topic names, message and service shapes, and every ``rclpy`` call you write are identical to real ROS 2; the only things renamed are the outer command-line tools (``ros2`` becomes ``simple-ros2``, and so on), since those are the install step being replaced, not knowledge worth transferring.

Based on ROS2 **Lyrical**.

The tutorial pages on this site are the same tutorials published by the real ROS 2 project, run against simple-ros instead of a real ROS 2 install.

What it is not
-----------------

Not a competing framework, and not aiming for performance, realism, or feature completeness beyond what the tutorials need. Where real ROS 2 and simple-ros diverge, it's always in service of dropping installation friction, never in the concepts or interface a learner sees.

Where to go from here
------------------------

For the fuller, more opinionated case for why this project exists, see :doc:`About-ROS`. To see which tutorials are actually runnable against simple-ros today, see :doc:`Development-Status`. To install it, see :doc:`Installation`.
