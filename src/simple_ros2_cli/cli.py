import sys

from simple_ros2_cli.verbs import node, param, pkg, run, service, topic

_VERBS = {
    "run": run.run,
    "pkg": pkg.run,
    "node": node.run,
    "topic": topic.run,
    "service": service.run,
    "param": param.run,
}


def main(argv: list = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] not in _VERBS:
        print(f"usage: simple-ros2 <{'|'.join(_VERBS)}> ...", file=sys.stderr)
        return 1
    return _VERBS[argv[0]](argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main())
