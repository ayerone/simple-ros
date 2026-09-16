.. _DevelopmentStatus:

Development Status
===================

.. container:: simple-ros-banner

   This is :doc:`simple-ros </About-simple-ros>`, not the official `ROS 2 project <https://docs.ros.org/en/lyrical/>`__.

simple-ros is under active development. Not every tutorial on this site is runnable end-to-end yet. This page is the ground truth for what actually works today, kept current as new pieces land, so you don't have to guess whether a stuck command is your mistake or a feature we haven't built.

**Area: ROS-framework | Content-type: reference | Experience: beginner**

.. contents:: Contents
   :depth: 2
   :local:

What works today
------------------

Topics, services, and parameters are fully implemented, on top of a working ``turtlesim`` (a real ``tkinter`` window) and the ``simple-ros2`` command line tool. Concretely: nodes can publish and subscribe to topics, offer and call services, and declare/get/set parameters, all discovered peer-to-peer with no background daemon, exactly as described in the tutorials.

Platform support
------------------

Linux only, for now. macOS is untested but has no known blocker. Windows genuinely does not work: every node crashes on startup (the registry's socket-path fallback calls ``os.getuid()``, which doesn't exist on Windows), and ``turtle_teleop_key`` fails to even import (it uses the POSIX-only ``termios``/``tty`` modules for raw keyboard input). Neither is a deliberately-scoped-out feature the way, say, actions are; they're just unaddressed.

Tutorial-by-tutorial status
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Page
     - Status
     - Notes
   * - :doc:`Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment`
     - Works
     -
   * - :doc:`Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim`
     - Partial
     - Turtle control, spawn/kill, and pen/teleport services all work. The ``rqt`` Service Caller steps don't, since ``simple-rqt`` doesn't exist yet.
   * - :doc:`Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Nodes/Understanding-ROS2-Nodes`
     - Works
     -
   * - :doc:`Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics`
     - Partial
     - ``topic list``/``echo``/``pub``/``info`` work. ``topic hz`` and ``topic bw`` aren't implemented, and the ``rqt_graph`` step doesn't work (no ``simple-rqt-graph`` yet).
   * - :doc:`Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Services/Understanding-ROS2-Services`
     - Works
     -
   * - :doc:`Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Parameters/Understanding-ROS2-Parameters`
     - Partial
     - ``param list``/``get``/``set`` work. ``param dump`` and ``param load`` aren't implemented.
   * - :doc:`Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Actions/Understanding-ROS2-Actions`
     - Not yet
     - Actions aren't implemented at all: no action server/client, no ``rotate_absolute``, no ``action`` CLI verbs.
   * - :doc:`Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data/Recording-And-Playing-Back-Data`
     - Not yet
     - ``simple-ros2 bag`` doesn't exist.
   * - :doc:`Tutorials/Beginner-CLI-Tools/Launching-Multiple-Nodes/Launching-Multiple-Nodes`
     - Not yet
     - ``simple-ros2 launch`` and the Python launch API don't exist.
   * - :doc:`Tutorials/Beginner-CLI-Tools/Using-Rqt-Console/Using-Rqt-Console`
     - Not yet
     - ``simple-rqt-console`` doesn't exist.
   * - :doc:`Tutorials/Beginner-Client-Libraries/Colcon-Tutorial`
     - Not yet
     - ``simple-colcon`` doesn't exist.
   * - :doc:`Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace`
     - Not yet
     - Depends on ``simple-colcon`` and the overlay/underlay workspace layout, neither built yet.
   * - :doc:`Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package`
     - Not yet
     - ``simple-ros2 pkg create`` doesn't exist.
   * - :doc:`Tutorials/Beginner-Client-Libraries/Getting-Started-With-Ros2doctor`
     - Not yet
     - ``simple-ros2 doctor`` doesn't exist.
   * - :doc:`Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber`
     - Partial
     - The ``rclpy`` publisher/subscriber API works, but only as a standalone script; running it as an installed workspace package needs ``simple-colcon``.
   * - :doc:`Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Service-And-Client`
     - Partial
     - Same as above: the ``rclpy`` service/client API works as a script, not yet as a workspace package.
   * - :doc:`Tutorials/Beginner-Client-Libraries/Using-Parameters-In-A-Class-Python`
     - Partial
     - Same as above: parameter declaration/access works as a script, not yet as a workspace package.

CLI verb gaps
---------------

Within verb groups that otherwise work, a few individual verbs are still missing:

* ``topic hz``, ``topic bw``, ``topic find``
* ``service find``, ``service echo``
* ``param dump``, ``param load``
* ``interface show``

Entire command groups not yet built: ``action *``, ``launch``, ``bag``, ``doctor``, ``simple-colcon``, ``simple-rosdep`` (not even a stub yet), and all of ``simple-rqt``/``simple-rqt-graph``/``simple-rqt-console``.

Known cosmetic gaps
----------------------

* Service request/response ``__repr__`` shows the internal generated class name (e.g. ``_SpawnRequest``) instead of matching real ROS 2's ``turtlesim_msgs.srv.Spawn_Request`` style.
* ``/parameter_events`` and ``/rosout`` aren't implemented, so ``topic list`` shows fewer topics than real ROS 2's sample tutorial output.

Where to go from here
------------------------

If a tutorial's status above is "Works," it should behave exactly as written. If it's "Partial," expect a specific step to fail where noted above. If it's "Not yet," treat it as reading material until that milestone lands.
