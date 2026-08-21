# Session summary: docs scaffolding through Milestone 1 implementation

## Docs scaffolding

Copied the Beginner-CLI-Tools and Beginner-Client-Libraries tutorial trees verbatim from `github.com/ros2/ros2_documentation` (lyrical branch) into `source/`, plus `First-Steps.rst` and `Tutorials.rst`. Set up a minimal Sphinx build (`conf.py` at repo root, RTD theme, `sphinx-tabs`, a no-op `redirect-from` directive) so the docs actually render locally via `sphinx-build -b html -c . source build/html`.

Wrote two original pages: `About-ROS.rst` (our own opinionated take on what ROS is and why simple-ros exists, explicitly not a copy of upstream's page, linking out to the real one) and `Installation.rst` + `Installation/Ubuntu-Install-How-To.rst` (venv + pip install instructions, with a from-source fallback until the package is actually published).

Pruned aggressively to keep the doc set honest about scope:

- Removed the `Examples` section and any bullet pointing at `ros2/examples` (real ROS 2 code a simple-ros learner can't build).
- Removed every `How-To-Guides` reference across the tutorial pages (a whole other upstream section we're not building).
- Removed the `Tutorials/{Intermediate,Advanced,Demos,Miscellaneous}` toctree entries (confirmed they never actually rendered in the sidebar; Sphinx silently drops toctree entries to nonexistent docs, so this was pure warning cleanup).
- Removed the C++ tracks entirely: `Writing-A-Simple-Cpp-Publisher-And-Subscriber.rst`, `Writing-A-Simple-Cpp-Service-And-Client.rst`, `Using-Parameters-In-A-Class-CPP.rst`, `Pluginlib.rst` (fundamentally C++/CMake-shaped, no meaningful Python port).
- Removed `Custom-ROS2-Interfaces.rst` (real ROS 2 positions it as the capstone of Beginner-Client-Libraries, not core material, and it's almost entirely CMake/rosidl packaging mechanics rather than transferable concept).
- Swept every remaining page for dangling cross-references into `Concepts/*` and other upstream sections we don't have, trimming the link or the sentence/section it lived in.

End state: a warning-free Sphinx build, 7-page Beginner-Client-Libraries sequence (Colcon Tutorial through Getting Started With ros2doctor), full Beginner-CLI-Tools sequence intact.

## Architecture: CLAUDE.md

Built up `CLAUDE.md` as the living spec across several planning passes. Key decisions:

- **The central invariant**: user-facing parity with real ROS 2 (node/topic/service/message/action names, the `rclpy` API surface, field shapes) with a completely independent pure-Python implementation underneath. Not a code-level relationship to upstream, just an interface-level one.
- **Command renaming**: `ros2`→`simple-ros2`, `colcon`→`simple-colcon`, `rqt`→`simple-rqt`, etc. Everything else (node names, topic names, message shapes) stays identical.
- **No daemon, direct peer-to-peer**: a filesystem registry (just shared storage, never a running process) plus direct Unix domain socket connections between nodes.
- **Python-only scope for now**: the C++ tutorial tracks and Pluginlib are out, with rationale recorded.
- **Well-justified dependencies are fine**: PyYAML for CLI argument parsing, `pydot`/Graphviz planned for a future `simple-rqt-graph`. Simplicity of implementation wins over reinventing real work.
- **Reading real ROS 2 source is encouraged** for understanding behavior/logic, never for copying code. Recorded where to find it (`docs.ros.org` is bot-blocked; use the mirrored `.rst` on GitHub instead) and which upstream repos matter for which piece (`ros2cli` for CLI verb behavior, `rclpy` for the client library, `rosidl` for interface generation, etc.).
- **Error message convention**: mirror real ROS 2's wording first (verified, not invented), then append a `simple-ros:` line explaining what actually happened and how to fix it.

## Milestone 1: plan and implementation

Used plan mode for the first real implementation slice, pressure-tested by a Plan subagent specifically against the communication-layer design before finalizing. The review caught one real bug before any code existed (naive `**kwargs` reconstruction breaks nested dataclasses like `Twist`) and several concrete gotchas that got baked into the plan: event-triggered discovery (not just polling, so `topic echo` feels immediate against an already-running publisher), a `request_id` field for correlating async service calls, AF_UNIX's 108-byte path limit (socket files live under `$XDG_RUNTIME_DIR` or `/tmp`, not under the venv), and non-blocking sockets with per-connection write queues so a stalled peer can't hang the whole node.

Scope: topics, services, and parameters against a working turtlesim. Actions (and the `Understanding-ROS2-Actions` tutorial) deliberately deferred to a follow-up milestone.

### What got built

- `simple_ros_runtime/` (internal plumbing, not a real ROS 2 namespace): `serialization.py` (`to_wire`/`from_wire`, with recursive reconstruction of nested dataclasses and `List[dataclass]` fields), `registry.py` (filesystem registry under `sys.prefix`, atomic writes, self-healing stale-entry pruning via pid liveness checks), `transport.py` (one Unix domain socket per node, multiplexed by newline-delimited JSON envelope, single-threaded `selectors`-based `Reactor`), `errors.py` (the `ros_error()` convention).
- `rclpy/`: `Node`, `Publisher`/`Subscription`/`Service`/`Client`, `create_timer`, executors (`spin`/`spin_once`/`spin_until_future_complete`/`Future`), `Parameter`, `--ros-args --remap`/`--params-file` parsing. Discovery is event-triggered at declaration time, and a `"hello"` handshake lets both sides of a connection register it symmetrically (needed because a publisher is usually the one being connected *to*, not the one initiating).
- Hand-written built-in interfaces (not a general codegen pipeline, since custom interfaces are out of scope): `std_msgs`, `std_srvs`, `geometry_msgs`, `rcl_interfaces` (including the `get_parameters`/`set_parameters` services every node registers automatically), `example_interfaces`, `turtlesim_msgs`.
- `turtlesim/`: a tkinter-windowed `turtlesim_node` (spawn/kill/clear/reset/set_pen/teleport services, `cmd_vel`-driven physics, `pose`/`color_sensor` publishing, live background-color parameters) and `turtle_teleop_key` (raw-terminal arrow keys via `tty`/`termios`; rotation keys are a stub pending actions).
- `simple_ros2_cli/`: `run`, `pkg executables`, `node`, `topic` (list/echo/info/pub), `service` (list/type/call/info), `param` (list/get/set). `param list` reads the registry directly since it's already kept in sync; `param get`/`set` do real service calls.

### Verification

17 automated tests (serialization including the nested/list cases, registry write/scan/prune, transport framing including a deliberately-split-across-two-writes JSON line, and pub/sub/service round-trips over the real transport, including cross-thread tests that mirror the real two-separate-processes deployment topology).

Manually verified end-to-end against a real `simple-ros2 run turtlesim turtlesim_node` background process with a real tkinter window: `node list`/`topic list -t`/`service list` all correctly `/`-prefixed, `service call /spawn ...` spawning a second turtle and correctly rejecting a duplicate name with the real error text plus a simple-ros tip, `topic pub`/`topic echo` showing the turtle actually move across 156 real pose updates at ~60Hz, and `param get`/`set` changing `background_r` live. Also confirmed the registry self-heals: killing `turtlesim_node` with SIGTERM (no clean shutdown) left a stale registry entry and socket file that the next `simple-ros2 node list` call silently pruned.

### Bug found during verification (beyond what the design review caught)

Topic/service names weren't being resolved to absolute form (leading `/`), so `topic list` showed `turtle1/pose` instead of real ROS 2's `/turtle1/pose`. Fixed in `Node._remap()`, with the same fix mirrored in `--remap` key parsing so remap rules still match after normalization.

## Next steps

- Milestone 2: actions (`turtlesim_msgs/action/RotateAbsolute`, the teleop rotation keys, `Understanding-ROS2-Actions`).
- `simple-colcon` and workspace/package support for the rest of Beginner-Client-Libraries.
- Known cosmetic gaps not yet addressed: service request/response `__repr__` shows private class names (`_SpawnRequest` instead of something like `turtlesim_msgs.srv.Spawn_Request`); `/parameter_events` and `/rosout` aren't implemented, so `topic list` shows fewer topics than real ROS 2's sample tutorial output.
