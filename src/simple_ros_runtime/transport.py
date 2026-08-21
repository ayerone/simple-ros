"""Unix domain socket transport: framing, non-blocking I/O, and the reactor.

One socket per node, multiplexed by envelope rather than one socket per
topic/service. Envelopes are newline-delimited JSON: compact JSON never
contains a raw newline, so this framing is safe and trivially inspectable
by hand (e.g. with ``nc``).

``Connection`` owns the framing and backpressure-safe write queue for one
socket. ``Reactor`` is the single-threaded ``selectors``-based event loop:
it accepts inbound connections, drives reads/writes on every connection,
and fires due timers. It knows nothing about topics/services/parameters;
that graph-matching logic lives in ``rclpy.node.Node``, which uses
``Reactor.connect`` and ``Reactor.send`` as its transport primitives.
"""

import dataclasses
import json
import selectors
import socket
import time
from collections import deque
from pathlib import Path
from typing import Callable, Iterator, Optional

_RECV_CHUNK = 65536


class Connection:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.on_close: Optional[Callable[["Connection"], None]] = None
        self._read_buf = bytearray()
        self._write_queue: deque[bytes] = deque()

    def feed(self, chunk: bytes) -> Iterator[dict]:
        """Accumulate a chunk and yield every complete envelope it completes.

        recv() gives no message-boundary guarantees: one line can span
        multiple chunks, and one chunk can contain several lines (e.g. a
        burst of pose updates). Never assume one envelope per recv().
        """
        self._read_buf.extend(chunk)
        while b"\n" in self._read_buf:
            line, _, rest = self._read_buf.partition(b"\n")
            self._read_buf = bytearray(rest)
            if line:
                yield json.loads(line.decode("utf-8"))

    def queue(self, envelope: dict) -> None:
        self._write_queue.append(json.dumps(envelope).encode("utf-8") + b"\n")

    def has_pending_writes(self) -> bool:
        return bool(self._write_queue)

    def flush(self) -> None:
        """Write as much of the queue as the socket will currently accept.

        A BlockingIOError here means "still queued, try again once writable"
        -- not an error. A slow peer must never be able to block this
        process via a naive sendall().
        """
        while self._write_queue:
            data = self._write_queue[0]
            try:
                sent = self.sock.send(data)
            except BlockingIOError:
                return
            if sent < len(data):
                self._write_queue[0] = data[sent:]
                return
            self._write_queue.popleft()


@dataclasses.dataclass
class _Timer:
    deadline: float
    period: float
    callback: Callable[[], None]
    one_shot: bool

    def cancel(self) -> None:
        self.period = -1  # sentinel checked by Reactor before firing again


class Reactor:
    """Single-threaded selectors-based event loop for one node's socket."""

    def __init__(self, listen_path: Path):
        self._selector = selectors.DefaultSelector()
        self._listen_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listen_sock.setblocking(False)
        self._listen_sock.bind(str(listen_path))
        self._listen_sock.listen()
        self._selector.register(self._listen_sock, selectors.EVENT_READ, data=None)
        self._connections: dict[int, Connection] = {}
        self._timers: list[_Timer] = []
        self.on_envelope: Optional[Callable[[dict, Connection], None]] = None
        self.on_accept: Optional[Callable[[Connection], None]] = None

    def connect(self, socket_path: str) -> Connection:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(socket_path)
        sock.setblocking(False)
        conn = Connection(sock)
        self._selector.register(sock, selectors.EVENT_READ, data=conn)
        self._connections[sock.fileno()] = conn
        return conn

    def send(self, conn: Connection, envelope: dict) -> None:
        conn.queue(envelope)
        self._flush_and_update(conn)

    def add_timer(self, period: float, callback: Callable[[], None], one_shot: bool = False) -> _Timer:
        timer = _Timer(deadline=time.monotonic() + period, period=period, callback=callback, one_shot=one_shot)
        self._timers.append(timer)
        return timer

    def run_soon(self, callback: Callable[[], None]) -> None:
        """Schedule a one-shot callback for the very next loop iteration."""
        self.add_timer(0.0, callback, one_shot=True)

    def _accept(self) -> None:
        while True:
            try:
                client_sock, _ = self._listen_sock.accept()
            except BlockingIOError:
                return
            client_sock.setblocking(False)
            conn = Connection(client_sock)
            self._selector.register(client_sock, selectors.EVENT_READ, data=conn)
            self._connections[client_sock.fileno()] = conn
            if self.on_accept:
                self.on_accept(conn)

    def _close_connection(self, conn: Connection) -> None:
        try:
            self._selector.unregister(conn.sock)
        except (KeyError, ValueError):
            pass
        self._connections.pop(conn.sock.fileno(), None)
        conn.sock.close()
        if conn.on_close:
            conn.on_close(conn)

    def _flush_and_update(self, conn: Connection) -> None:
        try:
            conn.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            self._close_connection(conn)
            return
        events = selectors.EVENT_READ
        if conn.has_pending_writes():
            events |= selectors.EVENT_WRITE
        try:
            self._selector.modify(conn.sock, events, data=conn)
        except (KeyError, ValueError):
            pass

    def _fire_due_timers(self) -> None:
        now = time.monotonic()
        for timer in list(self._timers):
            if timer.period < 0:  # cancelled
                self._timers.remove(timer)
                continue
            if timer.deadline <= now:
                timer.callback()
                if timer.one_shot:
                    if timer in self._timers:
                        self._timers.remove(timer)
                else:
                    timer.deadline = now + timer.period

    def _next_timeout(self) -> float:
        if not self._timers:
            return 1.0
        now = time.monotonic()
        soonest = min(t.deadline for t in self._timers)
        return max(0.0, min(soonest - now, 1.0))

    def spin_once(self, timeout: Optional[float] = None) -> None:
        if timeout is None:
            timeout = self._next_timeout()
        for key, mask in self._selector.select(timeout):
            if key.data is None:
                self._accept()
                continue
            conn: Connection = key.data
            if mask & selectors.EVENT_READ:
                try:
                    chunk = conn.sock.recv(_RECV_CHUNK)
                except BlockingIOError:
                    chunk = None
                except (ConnectionResetError, OSError):
                    self._close_connection(conn)
                    continue
                if chunk == b"":
                    self._close_connection(conn)
                    continue
                if chunk and self.on_envelope:
                    for envelope in conn.feed(chunk):
                        self.on_envelope(envelope, conn)
            if mask & selectors.EVENT_WRITE:
                self._flush_and_update(conn)
        # Timers are checked every iteration regardless of why select()
        # returned -- fd activity and a due timer can coincide.
        self._fire_due_timers()

    def spin(self, should_continue: Callable[[], bool] = lambda: True) -> None:
        while should_continue():
            self.spin_once()

    def close(self) -> None:
        for conn in list(self._connections.values()):
            self._close_connection(conn)
        self._selector.close()
        self._listen_sock.close()
