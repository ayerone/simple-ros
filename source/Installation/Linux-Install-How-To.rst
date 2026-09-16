.. _LinuxInstallHowTo:

Installing on Linux - how-to
=============================

.. container:: simple-ros-banner

   This is :doc:`simple-ros </About-simple-ros>`, not the official `ROS 2 project <https://docs.ros.org/en/lyrical/>`__.

.. contents:: Contents
   :depth: 2
   :local:

Summary
-------

simple-ros is a single pip-installable Python package. There's no separate ``ros-<distro>-<package>`` step for individual tools; everything covered in the :doc:`Beginner tutorials </Tutorials>` comes from the one package.

Note: simple-ros isn't published to PyPI yet, so you should install it by cloning the repository.

Prerequisites
-------------

* Linux (any reasonably current distribution)
* Python 3.10 or newer, with the ``venv`` module available (see the `Basic Python setup <https://github.com/ayerone/simple-ros#basic-python-setup>`__ note in the project README if you don't have pip, etc installed already)
* ``git``

Steps
-----

1 Clone the repository
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  $ git clone https://github.com/ayerone/simple-ros.git
  $ cd simple-ros

2 Create and activate a virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  $ python3 -m venv .venv
  $ source .venv/bin/activate

.. note::

  Run the ``source`` command, from inside the ``simple-ros`` checkout, in every new terminal before ``simple-ros2`` is available, the same as sourcing a ROS 2 setup file.

3 Install simple-ros
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  $ pip install -e .

4 Verify the install
^^^^^^^^^^^^^^^^^^^^^

In one terminal, run a talker:

.. code-block:: console

  $ source .venv/bin/activate
  $ simple-ros2 run demo_nodes_py talker

In another terminal, run a listener:

.. code-block:: console

  $ source .venv/bin/activate
  $ simple-ros2 run demo_nodes_py listener

You should see the talker publishing messages and the listener hearing them.

Next steps
----------

After the installation is complete, you can proceed with :doc:`configuring your environment </Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment>`.

We recommend that you get familiar with key ROS concepts and check out the tutorials:

* :doc:`First steps with ROS - learning path </First-Steps>`
