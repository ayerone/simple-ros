# simple-ros

## What this project is

simple-ros is a from-scratch reimplementation of enough of ROS 2 (lyrical) to let a learner work through the Beginner tutorials without installing real ROS 2. The whole thing ships as one pip-installable Python package. Setup is: create a venv, `pip install` the package. Activating that venv stands in for sourcing a ROS 2 underlay (`source /opt/ros/{distro}/setup.bash`). From that point on, every command in the tutorials should look and feel like real ROS 2, just running against our own Python implementation instead of the real client libraries and DDS/RTPS middleware underneath.

The purpose is purely educational: let someone go through the beginner tutorials, build a real mental model of nodes/topics/services/actions/parameters, and then move to a real ROS 2 install where everything they learned (concepts, node graph vocabulary, message/service shapes, the rclpy API they wrote code against) carries over directly. Performance and efficiency are explicitly not goals here. Simplicity of implementation wins over speed or realism every time there's a tradeoff.

Every tutorial page we ship should carry a short note at the top: "simple-ros, an easily-installable package to learn real [ROS 2](link)". That note has not been added yet; it's a pending content task against the `.rst` files already in `source/Tutorials/`.

## The one invariant that matters most

**Everything a learner writes, reads, or types that refers to the ROS graph itself stays identical to real ROS 2.** This is about the user-facing interface, not the implementation: our code is plain Python, written independently of upstream's C++/Python client libraries, and owes nothing to how they built anything internally. What has to match is what a learner observes and types: package names (`turtlesim`), node names (`/turtlesim`, `/teleop_turtle`), topic names (`/turtle1/cmd_vel`), message/service/action types (`geometry_msgs/msg/Twist`, `turtlesim_msgs/srv/Spawn`, `turtlesim_msgs/action/RotateAbsolute`), field names, and the `rclpy` API surface (`Node`, `create_publisher`, `create_subscription`, `create_service`, `create_client`, `create_timer`, `declare_parameter`, `get_parameter`, `rclpy.spin`, etc. - same class/method/module names and call signatures). A learner's Python source files should be copy-pasteable into a real ROS 2 workspace with zero changes, even though our `rclpy` module is a from-scratch implementation, not a fork of theirs.

The only things that change are the outer command-line tool names, because those are the "install ROS 2" affordance we're replacing, not knowledge we want to transfer:

| Real ROS 2 | simple-ros |
|---|---|
| `ros2` | `simple-ros2` |
| `colcon` | `simple-colcon` |
| `rosdep` | `simple-rosdep` |
| `rqt` | `simple-rqt` |
| `rqt_console` (`ros2 run rqt_console rqt_console`) | `simple-rqt-console` |
| `rqt_graph` (`ros2 run rqt_graph rqt_graph`) | `simple-rqt-graph` |
| `ros2doctor` (`ros2 doctor`) | `simple-ros2 doctor` (subcommand, matches real usage) |
| `ament_python` / `ament_cmake` build type strings | `simple_ament_python` (see Python-only scope below; there is no cmake build type) |

Everything else in the tutorial text (node names, topic echoes, service calls, YAML parameter dumps, package.xml contents) reads the same in our docs as in upstream's.

## Scope: Python only, for now

Real ROS 2's beginner tutorials are written with parallel C++ and Python tracks. We are not implementing the C++ side:

- `Writing-A-Simple-Cpp-Publisher-And-Subscriber`, `Writing-A-Simple-Cpp-Service-And-Client`, `Using-Parameters-In-A-Class-CPP` are out of scope. Only the Python variants of each get a simple-ros implementation.
- `Pluginlib.rst` is excluded entirely. It's fundamentally about `dlopen`-style dynamic loading of shared libraries via `class_loader`/CMake; there's no meaningful Python analog that teaches the same real-ROS-2 skill, so reimplementing it would just be inventing a different lesson under the same name. If we want a "plugins" lesson later it should be scoped as a new decision, not a straight port.
- `ros2 pkg create --build-type ament_cmake` and CMakeLists.txt editing steps are out of scope. `ament_python` is the only supported build type.

One consequence: `Custom-ROS2-Interfaces.rst` in real ROS 2 requires an `ament_cmake` package (`rosidl_generate_interfaces()` in CMakeLists.txt) even when the interfaces are only consumed from Python. Since we have no CMake at all, our version needs a Python-native equivalent for declaring `.msg`/`.srv` files and generating code from them (see Interface generation below). This is a deliberate deviation from the literal upstream steps and that page's text will need editing to match, once we get to implementation.

## Distribution / workspace model

Two layers of "sourcing," matching upstream's underlay/overlay model:

1. **Underlay = the venv.** `python3 -m venv .venv && source .venv/bin/activate && pip install simple-ros` is the equivalent of installing ROS 2 and sourcing `/opt/ros/{distro}/setup.bash`. This is what makes `simple-ros2`, `simple-colcon`, etc. available on PATH, and makes `import rclpy` work.
2. **Overlay = a simple-colcon workspace**, exactly like upstream's `ros2_ws`. `simple-colcon build` in a workspace with a `src/` directory should still produce `build/`, `install/`, and `log/` directories, and `install/` should still contain a real `setup.bash` (and `local_setup.bash`) that a learner sources with `source install/setup.bash`, exactly as the `Creating-A-Workspace` tutorial describes. Under the hood this can just be pip-installing each `src/` package into the venv in editable mode plus writing a small generated shell script that adjusts `PATH`/`PYTHONPATH`, but the tutorial-facing behavior (the directories that appear, the sourcing step, overlay precedence over underlay) needs to hold up so that tutorial's lesson about workspaces still teaches something true of real ROS 2.

`ros2 pkg create` becomes `simple-ros2 pkg create --build-type simple_ament_python ...` and should scaffold the same file layout upstream describes for Python packages: `package.xml`, `resource/<package_name>`, `setup.cfg`, `setup.py`, `<package_name>/__init__.py`, `test/`.

## Communication: no daemon, direct node-to-node

Explicit requirement: no background broker/daemon process shuttling messages between nodes. Nodes talk to each other directly. Given there's no timing pressure, the simplest mechanism that satisfies "no daemon" and "direct" wins:

- A filesystem-based **registry** (not a process) under something like `$SIMPLE_ROS_HOME` (default `~/.simple_ros/` or similar), scoped by domain, where each running node/CLI-introspection-process writes a small file on startup advertising its node name and a Unix domain socket path it's listening on, plus what it publishes/subscribes/serves. This directory is just shared storage, never a running process reading and relaying anything.
- Discovery is peer-to-peer: a node (or a CLI tool like `simple-ros2 topic echo`) that wants to reach other nodes scans that directory to find candidate sockets, then connects **directly** to them. No message ever passes through a third process.
- Since nodes can start in any order, and there's nothing pushing "a new peer just appeared" notifications without a daemon, peers should poll the registry directory on a timer (fine given no timing constraints) to notice new/departed peers, matching real ROS 2's discovery-then-connect behavior closely enough for the tutorials to make sense.
- Topics: a subscriber's socket accepts connections from any publisher whose name/type match; the publisher writes each message to every currently-connected subscriber socket directly.
- Services and actions: a client connects directly to the server's socket found via the registry, and does the request/response (or goal/feedback/result) exchange over that connection.
- Parameters: implemented as ordinary services on the same per-node socket, exactly like real ROS 2 does under the hood (`/node/get_parameters`, `/node/set_parameters`, etc., which is why `ros2 service list` on a bare node already shows six parameter-related services in the real tutorials). This means `simple-ros2 param get/set/list/dump/load` can be built entirely on top of the same service-calling machinery as everything else, with no separate parameter transport.
- `simple-ros2 node/topic/service/action list/info/echo` are themselves just short-lived registry-scanning, socket-connecting clients, the same way `ros2 topic echo` spins up an ephemeral node in real ROS 2.

The Python package we ship needs to provide top-level importable modules matching real ROS 2's namespaces exactly, since that's what the invariant above requires: `rclpy` (with `rclpy.node.Node`, `rclpy.executors.ExternalShutdownException`, `rclpy.parameter.Parameter`, etc.), and message/service/action packages: `std_msgs.msg`, `std_srvs.srv`, `geometry_msgs.msg`, `rcl_interfaces.msg`/`.srv`, `example_interfaces.srv` (`AddTwoInts`), and `turtlesim_msgs.msg`/`.srv`/`.action`.

## Interface generation (custom msg/srv)

Real ROS 2 uses `rosidl_generate_interfaces()` (CMake) to turn `.msg`/`.srv` files into generated Python (and C++) classes. We need a Python-only equivalent: given a package with `msg/*.msg` and `srv/*.srv` files (plus a lightweight declaration, since we have no CMakeLists.txt to call `rosidl_generate_interfaces()` from), `simple-colcon build` should generate importable Python classes with the same field names/types and the same `Request`/`Response` (for srv) or `Goal`/`Result`/`Feedback` (for action) structure real ROS 2 generates, so `from tutorial_interfaces.msg import Num` and `from tutorial_interfaces.srv import AddThreeInts` work exactly like upstream's tutorial shows. `ros2 interface show <type>` needs to print the same field-listing format shown in the tutorials (request/response separated by `---`).

## turtlesim: exact behavior needed

This is the single most load-bearing piece, since nearly every Beginner-CLI-Tools tutorial runs against it. From reading the tutorial pages, `turtlesim_node` needs:

**Topics** (per turtle, default turtle is `turtle1`):
- `/turtle1/cmd_vel` [`geometry_msgs/msg/Twist`] - subscribed, drives the turtle
- `/turtle1/pose` [`turtlesim_msgs/msg/Pose`] - published continuously (tutorial shows ~59 Hz, but any steady rate is fine)
- `/turtle1/color_sensor` [`turtlesim_msgs/msg/Color`] - published continuously

**Services** (on the `/turtlesim` node):
- `/spawn` [`turtlesim_msgs/srv/Spawn`] - request `x, y, theta, name` (name optional, auto-generated like `turtle2` if empty), response `name`; errors if name already exists
- `/kill` [`turtlesim_msgs/srv/Kill`]
- `/clear` [`std_srvs/srv/Empty`] - clears drawn lines
- `/reset` [`std_srvs/srv/Empty`]
- `/turtle1/set_pen` [`turtlesim_msgs/srv/SetPen`] - `r, g, b` (0-255), `width`
- `/turtle1/teleport_absolute` [`turtlesim_msgs/srv/TeleportAbsolute`]
- `/turtle1/teleport_relative` [`turtlesim_msgs/srv/TeleportRelative`]
- plus the six standard parameter services every node gets for free (see Communication above)

**Actions:**
- `/turtle1/rotate_absolute` [`turtlesim_msgs/action/RotateAbsolute`] - goal `theta` (float32, radians), result `delta`, feedback `remaining`; must support cancellation and the "new goal aborts in-progress goal" behavior the Understanding-ROS2-Actions tutorial demonstrates

**Parameters** (on `/turtlesim`): `background_r`, `background_g`, `background_b` (ints, default `69, 86, 255`), controlling window background color live.

`turtle_teleop_key` needs to: publish `Twist` on `<remapped>/cmd_vel` from arrow keys, send `rotate_absolute` goals from the `G|B|V|C|D|E|R|T` keys (compass positions around `F` on a QWERTY layout), and cancel the in-flight goal on `F`. Must support `--ros-args --remap` the same way real ROS 2 executables do, since the Introducing-Turtlesim tutorial's whole "control a second turtle" task depends on remapping working.

## GUI scope

Two GUI surfaces get used across these tutorials: the turtlesim window itself, and `rqt` (used for its Service Caller plugin, `rqt_graph`, and `rqt_console`).

My default call, open to override: use `tkinter` (Python stdlib, no extra dependency, no GPU needed) for the turtlesim window, since it's used constantly and its visuals appear directly in tutorial screenshots we're keeping. For `rqt`, building a real Qt plugin framework clone is out of proportion to what the tutorials actually exercise. Instead, ship minimal standalone `simple-rqt-*` tools that cover exactly the tasks upstream's tutorials walk through and nothing more:

- `simple-rqt` with a bare Service Caller view (used in Introducing-Turtlesim to call `/spawn` and `/turtle1/set_pen` interactively)
- `simple-rqt-graph` showing nodes and topic/service/action connections (used in Understanding-ROS2-Topics to visualize the graph)
- `simple-rqt-console` as a log viewer with severity filtering (used in Using-Rqt-Console)

## `simple-ros2 bag`

No need to match the real `mcap`/`sqlite3` storage format. A simple recorded-messages format (e.g. JSON Lines: topic, type, timestamp, serialized payload, one per line, plus a `metadata.yaml` alongside) is enough to support `record`/`play`/`info` with reasonably faithful relative timing on playback (not hard-realtime, just "plays back in roughly the recorded order and pacing" so the turtle-path-replay demo in Recording-And-Playing-Back-Data still works). Service and action introspection/recording (`--service`, `--action`, `ros2 service echo`, `ros2 action echo`) both depend on those channels supporting an introspection hook; simplest approach is to have every service/action connection optionally mirror its request/response (or goal/feedback/result) traffic to any introspection listener, gated by a parameter the same way real ROS 2 gates it (`service_configure_introspection`, `action_server_configure_introspection`, etc.) so the tutorial's parameter-toggle steps still make sense.

## Full CLI surface to implement (from the tutorial pages we've copied in)

`simple-ros2`:
- `run <package> <executable> [--ros-args --remap ... --params-file ... --log-level ...]`
- `pkg create --build-type simple_ament_python [--node-name] [--license] [--dependencies]`, `pkg executables <package>`
- `node list`, `node info <node>`
- `topic list [-t]`, `topic echo <topic>`, `topic info <topic> [--verbose]`, `topic pub [--once] [-w N] [--rate N] <topic> <type> <yaml>`, `topic hz <topic>`, `topic bw <topic>`, `topic find <type>`
- `service list [-t]`, `service type <service>`, `service info <service> [--verbose]`, `service find <type>`, `service call <service> <type> [<yaml>]`, `service echo <service>`
- `action list [-t]`, `action type <action>`, `action info <action>`, `action send_goal [--feedback] <action> <type> <yaml>`, `action echo <action>`
- `param list`, `param get <node> <param>`, `param set <node> <param> <value>`, `param dump <node>`, `param load <node> <file>`
- `interface show <type>`
- `launch <package> <launch_file.py>` (Python launch files; XML/YAML launch formats are not required for the pages we've copied)
- `bag record [--topics ...|--all|--service ...|--all-services|--action ...|--all-actions] [-o name] [-d duration|-b size]`, `bag play [-i ...] [--publish-service-requests] [--send-actions-as-client]`, `bag info <bag>`
- `doctor [--report]`
- `plugin list` - only needed if we ever revisit Pluginlib; not required for current scope

`simple-colcon`: `build [--symlink-install] [--packages-select ...] [--packages-up-to ...]`, `test [--packages-select ...]`

`simple-rosdep`: `install -i --from-path src --rosdistro <distro> -y` can likely be closer to a no-op / trivial success message in simple-ros, since we don't have real OS package dependencies to resolve; still worth keeping the command so workspace-tutorial text ports unchanged.

## Tutorial pages already copied into this repo

`source/First-Steps.rst`, `source/Tutorials.rst`, all of `source/Tutorials/Beginner-CLI-Tools/` and `source/Tutorials/Beginner-Client-Libraries/` (see the per-page notes above for exclusions within that set: Pluginlib, and the C++ tracks of the pub/sub, service/client, and parameters pages).
