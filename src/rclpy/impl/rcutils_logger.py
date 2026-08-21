"""Console logging matching real ROS 2's ``[LEVEL] [node_name]: message`` format."""


class RcutilsLogger:
    def __init__(self, name: str):
        self._name = name

    def debug(self, msg: str) -> None:
        print(f"[DEBUG] [{self._name}]: {msg}")

    def info(self, msg: str) -> None:
        print(f"[INFO] [{self._name}]: {msg}")

    def warn(self, msg: str) -> None:
        print(f"[WARN] [{self._name}]: {msg}")

    def error(self, msg: str) -> None:
        print(f"[ERROR] [{self._name}]: {msg}")

    def fatal(self, msg: str) -> None:
        print(f"[FATAL] [{self._name}]: {msg}")
