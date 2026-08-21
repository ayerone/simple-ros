import sys

from simple_ros2_cli.verbs.run import executables_in_package


def run(argv: list) -> int:
    if len(argv) >= 2 and argv[0] == "executables":
        package = argv[1]
        for name in executables_in_package(package):
            print(f"{package} {name}")
        return 0
    print("usage: simple-ros2 pkg executables <package>", file=sys.stderr)
    return 1
