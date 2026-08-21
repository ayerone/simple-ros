# simple-ros

## What this project is

simple-ros is a from-scratch reimplementation of enough of ROS 2 (lyrical) to let a learner work through the Beginner tutorials without installing real ROS 2. The whole thing ships as one pip-installable Python package. Setup is: create a venv, `pip install` the package. Activating that venv stands in for sourcing a ROS 2 underlay (`source /opt/ros/{distro}/setup.bash`). From that point on, every command in the tutorials should look and feel like real ROS 2, just running against our own Python implementation instead of the real client libraries and DDS/RTPS middleware underneath.

The purpose is purely educational: let someone go through the beginner tutorials, build a real mental model of nodes/topics/services/actions/parameters, and then move to a real ROS 2 install where everything they learned (concepts, node graph vocabulary, message/service shapes, the rclpy API they wrote code against) carries over directly. Performance and efficiency are explicitly not goals here. Simplicity of implementation wins over speed or realism every time there's a tradeoff.

Everything under `source/` is sourced from the upstream ROS 2 documentation repo, [github.com/ros2/ros2_documentation](https://github.com/ros2/ros2_documentation), on the `lyrical` branch. That's also the repo behind `docs.ros.org` (see "Referencing real ROS 2 source code" below for how to fetch from it when the site itself is unreachable) and the place to look first for any other doc page we might want to pull in later.

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

Real ROS 2's beginner tutorials are written with parallel C++ and Python tracks. We are not implementing the C++ side, and the corresponding pages have been removed from `source/` (not just left unbuilt):

- `Writing-A-Simple-Cpp-Publisher-And-Subscriber.rst`, `Writing-A-Simple-Cpp-Service-And-Client.rst`, `Using-Parameters-In-A-Class-CPP.rst` are removed. Only the Python variant of each stays.
- `Pluginlib.rst` is removed. It's fundamentally about `dlopen`-style dynamic loading of shared libraries via `class_loader`/CMake; there's no meaningful Python analog that teaches the same real-ROS-2 skill, so reimplementing it would just be inventing a different lesson under the same name. If we want a "plugins" lesson later it should be scoped as a new decision, not a straight port.
- `Custom-ROS2-Interfaces.rst` is removed. In real ROS 2 it requires an `ament_cmake` package (`rosidl_generate_interfaces()` in CMakeLists.txt) even when the interfaces are only consumed from Python, and we have no CMake at all. The underlying concept (message/service types are just field lists in a text file, and you can define your own) is genuinely simple and worth teaching, but the tutorial as written is almost entirely CMake/`rosidl` packaging mechanics, which isn't something worth building a from-scratch interface-codegen system to reproduce faithfully. It's positioned as the last, capstone tutorial in real ROS 2's Beginner-Client-Libraries sequence, not core material. Candidate for a much shorter, simple-ros-native lesson later if we ever build custom interface support (see Interface generation below); not currently planned.
- `ros2 pkg create --build-type ament_cmake` and CMakeLists.txt editing steps are out of scope generally. `ament_python` (renamed `simple_ament_python`) is the only supported build type.

## Distribution / workspace model

Two layers of "sourcing," matching upstream's underlay/overlay model:

1. **Underlay = the venv.** `python3 -m venv .venv && source .venv/bin/activate && pip install simple-ros` is the equivalent of installing ROS 2 and sourcing `/opt/ros/{distro}/setup.bash`. This is what makes `simple-ros2`, `simple-colcon`, etc. available on PATH, and makes `import rclpy` work.
2. **Overlay = a simple-colcon workspace**, exactly like upstream's `ros2_ws`. `simple-colcon build` in a workspace with a `src/` directory should still produce `build/`, `install/`, and `log/` directories, and `install/` should still contain a real `setup.bash` (and `local_setup.bash`) that a learner sources with `source install/setup.bash`, exactly as the `Creating-A-Workspace` tutorial describes. Under the hood this can just be pip-installing each `src/` package into the venv in editable mode plus writing a small generated shell script that adjusts `PATH`/`PYTHONPATH`, but the tutorial-facing behavior (the directories that appear, the sourcing step, overlay precedence over underlay) needs to hold up so that tutorial's lesson about workspaces still teaches something true of real ROS 2.

`ros2 pkg create` becomes `simple-ros2 pkg create --build-type simple_ament_python ...` and should scaffold the same file layout upstream describes for Python packages: `package.xml`, `resource/<package_name>`, `setup.cfg`, `setup.py`, `<package_name>/__init__.py`, `test/`.

## Communication: no daemon, direct node-to-node

Explicit requirement: no background broker/daemon process shuttling messages between nodes. Nodes talk to each other directly. Given there's no timing pressure, the simplest mechanism that satisfies "no daemon" and "direct" wins:

Implemented as of Milestone 1 (`src/simple_ros_runtime/`, `src/rclpy/node.py`):

- A filesystem-based **registry** (not a process), under `Path(sys.prefix) / "var" / "simple_ros" / "domains" / <domain_id> / "nodes"` (`domain_id` from `SIMPLE_ROS_DOMAIN_ID`, default `"0"`). This is a deviation from an earlier draft of this doc that said `$SIMPLE_ROS_HOME`; scoping it to the active venv is better since it's self-cleaning (delete the venv, the registry's gone) and matches "the venv is the underlay." Each running node writes one JSON file on startup (and on every graph change) advertising its name, a uuid, its pid, its socket path, and what it publishes/subscribes/serves/calls, via `registry.write_node_info()` (atomic: temp file + `os.replace()`). This directory is just shared storage, never a running process reading and relaying anything.
- Socket **files** live somewhere short instead (`$XDG_RUNTIME_DIR/simple_ros/<uuid>.sock` or `/tmp/simple_ros-$UID/<uuid>.sock`), since AF_UNIX paths are capped at 108 bytes on Linux and a venv path can exceed that.
- Discovery is peer-to-peer and **event-triggered**, not purely polled: `create_publisher`/`create_subscription`/`create_client`/`create_service` each trigger an immediate one-shot registry scan + connect attempt (`Node._discover_peers()`), on top of a periodic backstop poll (every 0.5s, via a `Reactor` timer) that catches a peer appearing later. Purely polling would make `topic echo` visibly lag behind an already-running publisher, undermining the "immediate" feel the tutorials rely on.
- Transport is one Unix domain socket per node (not one per topic/service), multiplexed by a newline-delimited JSON envelope (`simple_ros_runtime/transport.py`'s `Reactor`/`Connection`): `{"kind": ..., "channel": ..., "type": ..., "request_id": ..., "data": {...}}`. Whichever side notices a match first connects out and sends a `"hello"` envelope carrying its uuid, so the accepting side can key that same connection into its own peer-connection table too; without this, a node that's only ever connected *to* (a publisher, typically) would have nothing to broadcast over.
- Topics: `Publisher.publish()` broadcasts to every currently-connected peer; receivers filter by `channel` against their own subscriptions. Simplicity over the narrowest possible fan-out.
- Services: a client connects directly to the server's socket found via the registry; `request_id` correlates responses to pending futures, since a client can have multiple in-flight `call_async()` requests over the same shared connection.
- Parameters: implemented as ordinary services on the same per-node socket (`get_parameters`/`set_parameters`, using `rcl_interfaces.msg`/`.srv` types), exactly like real ROS 2 does under the hood. `simple-ros2 param get/set` are real service calls through this; `simple-ros2 param list` reads the registry's `parameters` field directly instead, since that's already kept in sync and needs no live round-trip.
- `simple-ros2 node/topic/service list/info/echo/pub/call` are themselves short-lived registry-scanning, socket-connecting clients (named `_ros2cli_<pid>`, matching the real tutorials' ephemeral-node naming), the same way `ros2 topic echo` spins up an ephemeral node in real ROS 2. Actions are deferred to Milestone 2.

The Python package we ship needs to provide top-level importable modules matching real ROS 2's namespaces exactly, since that's what the invariant above requires: `rclpy` (with `rclpy.node.Node`, `rclpy.executors.ExternalShutdownException`, `rclpy.parameter.Parameter`, etc.), and message/service/action packages: `std_msgs.msg`, `std_srvs.srv`, `geometry_msgs.msg`, `rcl_interfaces.msg`/`.srv`, `example_interfaces.srv` (`AddTwoInts`), and `turtlesim_msgs.msg`/`.srv`/`.action`.

## Interface generation (built-in msg/srv/action types only)

With `Custom-ROS2-Interfaces.rst` out of scope (see above), we don't need a general `.msg`/`.srv`-file-to-Python-class codegen pipeline. What we do need is hand-written Python classes for the fixed set of built-in interfaces the tutorials we're keeping actually reference: `geometry_msgs/msg/Twist`, `std_msgs.msg`, `std_srvs/srv/Empty`, `rcl_interfaces` (parameter-related messages/services), `example_interfaces/srv/AddTwoInts`, and the `turtlesim_msgs` package (`Pose`, `Color`, `Spawn`, `Kill`, `SetPen`, `TeleportAbsolute`, `TeleportRelative`, `RotateAbsolute`). Same field names/types as real ROS 2 (see the turtlesim spec below for the exact shapes we've confirmed from the tutorial text), just hand-written instead of generated. `ros2 interface show <type>` still needs to print the same field-listing format shown in the tutorials (request/response separated by `---`), reading from whatever internal representation those hand-written classes carry their field info in.

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

Dependencies are fine when they're well justified; the goal is a simple and convenient implementation, not a zero-dependency one. `simple-rqt-graph` should use `pydot`/Graphviz for graph layout rather than us writing a layout algorithm from scratch, the same way real `rqt_graph` does.

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

`simple-colcon`: `build [--symlink-install] [--packages-select ...] [--packages-up-to ...]`, `test [--packages-select ...]`

`simple-rosdep`: `install -i --from-path src --rosdistro <distro> -y` can likely be closer to a no-op / trivial success message in simple-ros, since we don't have real OS package dependencies to resolve; still worth keeping the command so workspace-tutorial text ports unchanged.

## Referencing real ROS 2 source code

It's fine, and encouraged, to look at the actual upstream implementation when we're unsure how something is supposed to behave. The rule: read it for the *logic* (what algorithm it runs, what edge cases it handles, what a message's exact field layout is), not to copy code. Since our implementation language and communication model are both completely different from upstream's (pure Python, no DDS/RTPS, no daemon), there's rarely anything to copy anyway; what's valuable is the behavior. Good use: spawning an agent to read a specific upstream file or two and report back what logic it implements, then writing our own Python against that understanding.

`docs.ros.org` itself is behind bot-protection (Anubis) that blocks both browser-fetch and plain `curl`. Every page there is rendered from the `ros2/ros2_documentation` GitHub repo though, so fetch the equivalent `.rst` from `raw.githubusercontent.com/ros2/ros2_documentation/lyrical/...` instead (this is exactly how this repo's tutorial pages were sourced).

The full ROS 2 source tree is fetched upstream via `vcstool` against a repo manifest: `vcs import --input https://raw.githubusercontent.com/ros2/ros2/lyrical/ros2.repos src`. That manifest pulls in roughly 80 repos, most of which are irrelevant to us (rclcpp, rmw, DDS vendor implementations, etc.). It's more practical to fetch individual repos on GitHub as needed rather than doing the full checkout. The ones actually relevant to what we're building:

- **`ros2/rclpy`** - the real Python client library; the reference for `Node`, publishers/subscribers/services/actions/parameters/executors behavior
- **`ros2/ros2cli`** - the `ros2` command line tool itself, split into per-verb extension packages (`ros2topic`, `ros2service`, `ros2node`, `ros2param`, `ros2action`, `ros2interface`, `ros2pkg`, `ros2doctor`, `ros2launch`, ...). This is the most directly useful repo for `simple-ros2`'s CLI logic.
- **`ros2/rosbag2`** - reference for `simple-ros2 bag`'s record/play/info behavior
- **`ros2/rosidl`** and **`ros2/rosidl_python`** - reference for how `.msg`/`.srv`/`.action` files get turned into generated Python classes, for our interface-generation step
- **`ros2/common_interfaces`** (`geometry_msgs`, `std_msgs`, `sensor_msgs`, ...), **`ros2/rcl_interfaces`**, **`ros2/example_interfaces`** - the actual `.msg`/`.srv` definitions; ground truth for exact field names/types/ordering, better than reading them back out of tutorial prose
- **`ros/ros_tutorials`** - contains `turtlesim` itself; useful for exact spawn/teleport/pen/collision-with-wall behavior even though it's C++
- **`ros-visualization/rqt_graph`**, **`ros-visualization/rqt_console`**, **`ros-visualization/rqt`** - reference for what `simple-rqt-*` needs to reproduce
- **`colcon/colcon-core`** - reference for `simple-colcon`'s workspace/build/overlay behavior
- **`ros-infrastructure/rosdep`** - reference for `simple-rosdep`, though we expect to implement this as close to a no-op

## Tutorial pages already copied into this repo

`source/First-Steps.rst`, `source/Tutorials.rst`, all of `source/Tutorials/Beginner-CLI-Tools/`, and `source/Tutorials/Beginner-Client-Libraries/` minus the removed pages listed above (Pluginlib, the C++ pub/sub and service/client and parameters pages, Custom-ROS2-Interfaces). Also `source/About-ROS.rst` and `source/Installation.rst` + `source/Installation/Ubuntu-Install-How-To.rst`, which are our own original content, not copied from upstream.

Every remaining page has had its dangling cross-references into upstream sections we haven't copied (`How-To-Guides`, `Concepts`, `Tutorials/Intermediate`, `Tutorials/Demos`, anchors inside upstream's fuller Installation guide) trimmed out, dropping the surrounding sentence or section where the link was the only content. The Sphinx build is warning-free as of this pass; if a future content pull-in reintroduces one of those upstream sections, re-add the specific links back rather than leaving them dangling.
