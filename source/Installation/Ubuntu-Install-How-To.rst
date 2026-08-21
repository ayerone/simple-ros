.. _UbuntuInstallHowTo:

Installing on Ubuntu - how-to
==============================

**Goal:** Get simple-ros installed in a virtual environment and ready to work through the tutorials.

**Time:** 5 minutes

.. contents:: Contents
   :depth: 2
   :local:

Summary
-------

simple-ros is a single pip-installable Python package. There's no separate ``ros-<distro>-<package>`` install step for individual tools; everything covered in the :doc:`Beginner tutorials </Tutorials>` comes from the one package.

A Python virtual environment stands in for a ROS 2 "distro" install here. Creating and activating one is the whole installation step; activating it in a new terminal is simple-ros's equivalent of sourcing a ROS 2 underlay's ``setup.bash``, and you'll see that pattern again once you reach :doc:`Configuring environment </Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment>`.

Prerequisites
-------------

* Ubuntu (any reasonably current release)
* Python 3.10 or newer
* The ``venv`` module, which ships with Python but is split into a separate Ubuntu package

Steps
-----

1 Install prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  $ sudo apt update
  $ sudo apt install python3-venv python3-pip

2 Create a virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pick a location for it, the same way you'd pick a location for a ROS 2 workspace. This guide uses ``~/simple_ros_venv``:

.. code-block:: console

  $ python3 -m venv ~/simple_ros_venv

3 Activate it
^^^^^^^^^^^^^^

.. code-block:: console

  $ source ~/simple_ros_venv/bin/activate

.. note::

  You'll need to run this command in every new terminal before ``simple-ros2`` and the other simple-ros commands are available, exactly like sourcing a ROS 2 setup file. You can add it to your shell startup script (``~/.bashrc``) if you don't want to repeat it, the same tradeoff described in :doc:`Configuring environment </Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment>`.

4 Install simple-ros
^^^^^^^^^^^^^^^^^^^^^

.. tabs::

  .. group-tab:: From PyPI

    Once simple-ros is published, this is the normal path:

    .. code-block:: console

      $ pip install simple-ros

  .. group-tab:: From source

    Until then, or if you want an editable checkout to modify, clone the repository and install it in editable mode:

    .. code-block:: console

      $ git clone <REPO_URL> ~/simple_ros_src
      $ pip install -e ~/simple_ros_src

    Replace ``<REPO_URL>`` with wherever this repository ends up hosted.

5 Verify the install
^^^^^^^^^^^^^^^^^^^^^

With the virtual environment still active, check that the ``simple-ros2`` command is on your path:

.. code-block:: console

  $ simple-ros2 doctor

A working install reports its checks the same way real ROS 2's ``ros2 doctor`` does.

Next steps
----------

With simple-ros installed, continue to :doc:`First steps with ROS - learning path </First-Steps>`, or jump straight into :doc:`Configuring environment </Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment>` if you're already familiar with the concepts and just want to start typing commands.
