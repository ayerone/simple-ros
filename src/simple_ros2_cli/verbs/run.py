import sys
from importlib.metadata import entry_points

from simple_ros_runtime.errors import ros_error


def _executables() -> dict:
    return {ep.name: ep for ep in entry_points(group="simple_ros2.executables")}


def executables_in_package(package: str) -> list:
    eps = _executables()
    return sorted(name.split(":", 1)[1] for name in eps if name.split(":", 1)[0] == package)


def run(argv: list) -> int:
    if len(argv) < 2:
        print("usage: simple-ros2 run <package> <executable> [--ros-args ...]", file=sys.stderr)
        return 1
    package, executable, *rest = argv
    eps = _executables()
    key = f"{package}:{executable}"
    ep = eps.get(key)
    if ep is None:
        if executables_in_package(package):
            print(
                ros_error(
                    f"No executable found '{executable}' in package '{package}'",
                    f"run 'simple-ros2 pkg executables {package}' to see what's actually available",
                ),
                file=sys.stderr,
            )
        else:
            print(
                ros_error(
                    f"Package '{package}' not found",
                    "check the spelling, or that it's been built with simple-colcon and the workspace is sourced",
                ),
                file=sys.stderr,
            )
        return 1
    ep.load()(rest)
    return 0
