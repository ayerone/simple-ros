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
* Python 3.10 or newer, with the ``venv`` module available (on a minimal Ubuntu install this can mean ``sudo apt install python3-venv python3-pip`` first; see the `Basic Python setup <https://github.com/ayerone/simple-ros#basic-python-setup>`__ note in the project README if you're not sure)
* ``git``

Steps
-----

simple-ros isn't published to PyPI yet, so it's installed from a clone of the repository rather than with a bare ``pip install simple-ros``.

1 Clone the repository
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  $ git clone https://github.com/ayerone/simple-ros.git
  $ cd simple-ros

2 Create a virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create it inside the checkout, the same way a ROS 2 workspace's ``build``/``install`` directories live alongside its ``src``:

.. code-block:: console

  $ python3 -m venv .venv

3 Activate it
^^^^^^^^^^^^^^

.. code-block:: console

  $ source .venv/bin/activate

.. note::

  You'll need to run this command, from inside the ``simple-ros`` checkout, in every new terminal before ``simple-ros2`` and the other simple-ros commands are available, exactly like sourcing a ROS 2 setup file. You can add it to your shell startup script (``~/.bashrc``) if you don't want to repeat it, the same tradeoff described in :doc:`Configuring environment </Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment>`.

4 Install simple-ros
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

  $ pip install -e .

Editable mode (``-e``) means edits to the checkout take effect without reinstalling. Once simple-ros is published, ``pip install simple-ros`` into an activated virtual environment will work too, without needing a clone at all.

5 Verify the install
^^^^^^^^^^^^^^^^^^^^^

Run a talker and a listener to check that two independent nodes can find each other and pass messages:

#. In one terminal, from inside the ``simple-ros`` checkout, activate the virtual environment, then run the talker:

   .. code-block:: console

     $ source .venv/bin/activate
     $ simple-ros2 run demo_nodes_py talker

#. In another terminal, from inside the same ``simple-ros`` checkout, activate the virtual environment, then run the listener:

   .. code-block:: console

     $ source .venv/bin/activate
     $ simple-ros2 run demo_nodes_py listener

   You should see the talker saying that it's publishing messages and the listener saying that it hears those messages.

Next steps
----------

With simple-ros installed, continue to :doc:`First steps with ROS - learning path </First-Steps>`, or jump straight into :doc:`Configuring environment </Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment>` if you're already familiar with the concepts and just want to start typing commands.
