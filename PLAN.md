# simple-ros: roadmap

Everything below is not yet built. This is a checklist/sequencing document, not the spec; behavioral detail for each piece (exact field shapes, message formats, CLI flag semantics) lives in `CLAUDE.md`, which this file points back to rather than duplicates. Milestone 1 (topics, services, parameters, a working tkinter turtlesim, and the `simple-ros2` CLI verbs that support them) is done; see `dev_log/2026-08-21-session-summary.md` for what that covered.

## Milestone 2: actions

Unlocks `Understanding-ROS2-Actions.rst`.

- `turtlesim_msgs/action/RotateAbsolute` (goal `theta`, result `delta`, feedback `remaining`).
- `rclpy` action API: an action-server/action-client pair analogous to the existing service Server/Client, but with a goal/feedback/result exchange instead of a single request/response, over the same per-node transport (see CLAUDE.md's turtlesim spec section for the exact behavior, including cancellation and "a new goal aborts an in-progress goal").
- `turtle_teleop_key`: wire up the `G|B|V|C|D|E|R|T` rotate-to-absolute-orientation keys and `F` to cancel (currently a no-op stub, see the module docstring in `src/turtlesim/turtle_teleop_key.py`).
- `simple-ros2 action list [-t]`, `action type`, `action info`, `action send_goal [--feedback]`, `action echo`.

## Milestone 3: launch

Unlocks `Launching-Multiple-Nodes.rst` (the launch file itself, `multisim.launch.py`, is already sitting in `source/Tutorials/Beginner-CLI-Tools/Launching-Multiple-Nodes/launch/`, unrunnable until this exists).

- A minimal Python launch API (`LaunchDescription`, a `Node` launch action at least) that a `.launch.py` file can import and that `simple-ros2 launch` can execute -- this needs its own design pass, CLAUDE.md doesn't detail it beyond "Python launch files; XML/YAML not required for the pages we've copied."
- `simple-ros2 launch <package> <launch_file.py>`.

## Milestone 4: bag

Unlocks `Recording-And-Playing-Back-Data.rst`.

- `simple-ros2 bag record/play/info` against a JSON-Lines storage format (see CLAUDE.md's `simple-ros2 bag` section for the exact approach).
- Service/action introspection hooks gated by parameters (`service_configure_introspection`, `action_server_configure_introspection`, etc.), needed for the tutorial's `service echo`/`action echo` steps.

## Milestone 5: colcon and packaging

Unlocks `Colcon-Tutorial.rst`, `Creating-A-Workspace/Creating-A-Workspace.rst`, `Creating-Your-First-ROS2-Package.rst`, and (since the underlying `rclpy` functionality already works) makes `Writing-A-Simple-Py-Publisher-And-Subscriber.rst`, `Writing-A-Simple-Py-Service-And-Client.rst`, and `Using-Parameters-In-A-Class-Python.rst` runnable as real workspace packages rather than only as scripts.

- `simple-colcon build [--symlink-install] [--packages-select ...] [--packages-up-to ...]`, `simple-colcon test`.
- `simple-ros2 pkg create --build-type simple_ament_python [--node-name] [--license] [--dependencies]`, scaffolding the same file layout upstream's Python packages use (`package.xml`, `resource/<name>`, `setup.cfg`, `setup.py`, `<name>/__init__.py`, `test/`).
- The overlay/underlay workspace model: `simple-colcon build` needs to produce real `build/`, `install/`, `log/` directories and a real `install/setup.bash`/`local_setup.bash` a learner can source, with overlay-over-underlay precedence actually holding (see CLAUDE.md's "Distribution / workspace model" section). Must be a real `pip install -e` per package under the hood, not a bare `PYTHONPATH` shove, or `simple-ros2 run`'s `importlib.metadata.entry_points()` lookup won't see packages built this way (noted during Milestone 1 planning).

## Milestone 6: doctor

Unlocks `Getting-Started-With-Ros2doctor.rst`.

- `simple-ros2 doctor [--report]`.

## Milestone 7: rqt tools

Unlocks the `rqt` portions of `Introducing-Turtlesim.rst` (Service Caller), the `rqt_graph` portion of `Understanding-ROS2-Topics.rst`, and `Using-Rqt-Console.rst`.

- `simple-rqt`: a bare Service Caller view.
- `simple-rqt-graph`: node/topic/service/action graph, using `pydot`/Graphviz for layout (a deliberately accepted dependency, see CLAUDE.md's GUI scope section).
- `simple-rqt-console`: a log viewer with severity filtering.

## Smaller gaps within already-built CLI verb groups

Not full milestones, just verbs listed in CLAUDE.md's "Full CLI surface" that Milestone 1 didn't get to:

- `topic hz`, `topic bw`, `topic find`
- `service find`, `service echo`
- `interface show <type>`
- `param dump`, `param load`

## Known cosmetic gaps (noted during Milestone 1 verification, not yet fixed)

- Service request/response `__repr__` shows the private generated class name (e.g. `_SpawnRequest`) instead of something matching real ROS 2's `turtlesim_msgs.srv.Spawn_Request` style.
- `/parameter_events` and `/rosout` aren't implemented, so `topic list` shows fewer topics than real ROS 2's sample tutorial output.
- `simple-rosdep` doesn't exist yet even as a near-no-op stub (CLAUDE.md's intended shape: keep the command so workspace-tutorial text ports unchanged, since we have no real OS package dependencies to resolve).

## Content tasks (not code)

- Add the pending "simple-ros, an easily-installable package to learn real ROS 2" banner note to the top of every tutorial page under `source/Tutorials/` (mentioned in `CLAUDE.md` as still outstanding).
- `Custom-ROS2-Interfaces.rst`: a candidate for a much shorter, simple-ros-native lesson someday if custom interface support ever gets built, per CLAUDE.md's scope section. Not currently planned; revisit only as a deliberate new decision.

## Infrastructure loose ends

- `source/Installation/Ubuntu-Install-How-To.rst` has a literal `<REPO_URL>` placeholder for the "install from source" fallback -- fill in once this repo has a real remote.
- Not yet published to PyPI; the install docs already describe both paths (PyPI once published, from-source clone until then).
