.. _InstallationGuide:

Installation
============

simple-ros installs nothing like real ROS 2. There's no system package manager step, no distro archive to unpack, and no separate build toolchain to set up first. It's a normal Python package: create a virtual environment, install it, and you're ready to work through the tutorials.

.. toctree::
   :maxdepth: 1

   Installation/Linux-Install-How-To

Which install should you choose?
---------------------------------

Linux is the only platform simple-ros targets right now (see :doc:`Development-Status` for the macOS/Windows gap). The :doc:`Linux how-to <Installation/Linux-Install-How-To>` isn't distro-specific beyond its one optional ``apt`` step, so it should translate directly to any distribution.

Related content
----------------

Once simple-ros is installed, head to :doc:`First-Steps` for a guided path through the tutorials, or straight to :doc:`Tutorials` if you'd rather browse.
