"""Module-level state set by rclpy.init(args) and read by Node.__init__.

Real rclpy threads --ros-args (remapping, a params file, a log level)
through a global/thread-local context that Node() reads from implicitly
after init() has run. This project only ever has one Node per process in
the tutorials it targets, so a plain module global is enough.
"""

_remaps: dict[str, str] = {}
_params_file: str | None = None
_log_level: str | None = None


def reset() -> None:
    global _remaps, _params_file, _log_level
    _remaps = {}
    _params_file = None
    _log_level = None


def set_from_args(argv: list[str]) -> None:
    global _remaps, _params_file, _log_level
    remaps: dict[str, str] = {}
    params_file = None
    log_level = None
    if "--ros-args" in argv:
        i = argv.index("--ros-args") + 1
        while i < len(argv):
            token = argv[i]
            if token in ("--remap", "-r"):
                i += 1
                old, _, new = argv[i].partition(":=")
                # __node/__ns are special (not topic/service names); every
                # other key must match the absolute form Node._remap()
                # normalizes real names to before it looks a remap up.
                if not old.startswith("__") and not old.startswith("/"):
                    old = "/" + old
                remaps[old] = new
            elif token == "--params-file":
                i += 1
                params_file = argv[i]
            elif token == "--log-level":
                i += 1
                log_level = argv[i]
            i += 1
    _remaps = remaps
    _params_file = params_file
    _log_level = log_level


def remaps() -> dict[str, str]:
    return dict(_remaps)


def params_file() -> str | None:
    return _params_file


def log_level() -> str | None:
    return _log_level
