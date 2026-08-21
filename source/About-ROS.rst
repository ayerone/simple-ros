.. _AboutROS:

About ROS
=========

This is not the official "About ROS" page. It's our own, and it says what we actually think, including the parts the official version is too diplomatic to say out loud. If you want the real one, `Open Robotics' official About ROS page <https://docs.ros.org/en/lyrical/About-ROS.html>`__ is where the rest of this documentation set otherwise points.

**Area: ROS-framework | Content-type: opinion | Experience: beginner**

.. contents:: Contents
   :depth: 2
   :local:

What ROS actually is
---------------------

ROS (Robot Operating System) is not an operating system. It's a messaging framework and a pile of conventions: a way for a bunch of independent programs ("nodes") to find each other and exchange structured data over topics, services, and actions, plus a shared vocabulary (packages, interfaces, parameters, launch files) for describing how those programs fit together into a robot. That's genuinely the whole idea. Everything else, the simulators, the navigation stacks, the driver packages, is built on top of that one idea.

It's a good idea. Loosely-coupled processes talking over well-typed messages is a sound way to build a system with a camera driver written by one team, a planner written by another, and a motor controller written by a third, none of whom have to agree on a programming language or even be running on the same machine.

The part the official pitch undersells
----------------------------------------

Getting to the point where you can *feel* that good idea is unreasonably hard for a beginner. A real ROS 2 install means picking a Tier 1 platform, matching a specific Ubuntu LTS to a specific distro, pulling in a DDS implementation you didn't ask for and won't understand for months, and debugging discovery issues that have nothing to do with the code you wrote. None of that teaches you anything about nodes, topics, or services. It's just friction between you and the concepts.

That gap, between "I want to learn what a ROS topic is" and "I have successfully installed a robotics middleware stack", is the entire reason this project exists.

What simple-ros actually is
-----------------------------

simple-ros is a deliberately unfaithful reimplementation. We threw out everything that makes ROS 2 hard to install and kept everything that makes it worth learning:

* No DDS, no RMW implementations, no discovery configuration. Nodes just find each other directly.
* No system packages, no distro archives. It's ``pip install`` in a virtual environment.
* No daemon process quietly doing work you can't see.

What we did *not* touch is the part that actually matters to you as a learner: node names, topic names, message and service shapes, and the ``rclpy`` API you write code against are all the same as real ROS 2. Every command you type and every line of Python you write here should still work, unmodified, against a real ROS 2 install. We're teaching you the real interface, with a much shorter and much less painful on-ramp bolted onto the front of it.

Why keep the name "ROS" in ours at all
----------------------------------------

Because the goal isn't to build a competing framework. It's to get you fluent enough in ROS 2's actual vocabulary, nodes, topics, services, actions, parameters, that when you do install the real thing, none of it is unfamiliar. simple-ros is scaffolding, not a destination.

Where to go from here
------------------------

If you want the unabridged, unopinionated version of this page, read `Open Robotics' About ROS <https://docs.ros.org/en/lyrical/About-ROS.html>`__. If you'd rather just get started, head to :doc:`Installation` and then :doc:`First-Steps`.
