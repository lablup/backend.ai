"""The container log writer — our equivalent of dockerd's log driver.

The Docker backend does not write container logs itself: dockerd owns the write end of the
container's stdout and runs a log driver over it, which is what gives it max-size/max-file rotation
a container can never overrun.

containerd offers the same thing and we were not using it. Handed a plain path, the shim appends to
it forever and nobody rotates it. Handed a `binary://` log URI, the shim instead *starts this
program* and pipes the container's stdout and stderr into it — so we own the write end, exactly as
dockerd does, and rotation becomes ordinary: fill a file, rename it aside, open a new one, delete
the oldest. The cap is hard, and nothing is dropped.

The lifetime matters as much as the mechanism. This process is a child of the shim, not of the
agent: it lives and dies with the container, so an agent restart cannot interrupt it and cannot
block the container's stdout. That is what ruled out the obvious alternative of having the agent
read a FIFO itself.

The shim's contract (containerd's pkg/process binaryIO):
  - fd 3 is the container's stdout, fd 4 its stderr; both reach EOF when the container exits.
  - fd 5 is a "ready" pipe. containerd holds the task in 'created' until it closes, so we close it
    as soon as we can accept output — and not before.
  - CONTAINER_ID names the container.

STANDARD LIBRARY ONLY, and run by path rather than as a module. containerd execs this directly, in
a bare interpreter, at the moment a container starts; importing the agent package here would drag
the entire agent (aiotools, aiohttp, the plugin stack) into every container's logger and turn any
import error in the agent into a container that cannot start.
"""

from __future__ import annotations

import argparse
import os
import selectors
import sys
from pathlib import Path

# Docker's max-file: the active log plus (LOG_FILE_COUNT - 1) rotated ones. The Docker backend
# hard-codes 5 and derives max-size from it, so the same `container_logs.max_length` buys the same
# window on both backends. `logs.py` reads these back — a test pins the two to each other.
LOG_FILE_COUNT = 5

_STDOUT_FD = 3  # fixed by containerd's binaryIO, not by us
_STDERR_FD = 4
_READY_FD = 5

_READ_SIZE = 64 * 1024


def rotated_path(active: Path, index: int) -> Path:
    """`k.log` -> `k.log.1`, `k.log.2`, ... — the names Docker's driver uses."""
    return active.with_name(f"{active.name}.{index}")


def max_file_size(max_total_bytes: int) -> int:
    """Docker's max-size: the total budget split across max-file files."""
    return max(1, max_total_bytes // LOG_FILE_COUNT)


class RotatingLog:
    """Append to the active log, rolling it over the way Docker's driver does.

    We hold the file open, so rotation is the ordinary kind: close, shift the rotated files along,
    drop the oldest, open a fresh active file. Nothing is lost, and the cap is hard — no write can
    take a file past max-size, because we are the one writing it.
    """

    def __init__(self, active: Path, max_total_bytes: int) -> None:
        self._active = active
        self._max_size = max_file_size(max_total_bytes)
        self._active.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(self._active, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        self._size = os.fstat(self._fd).st_size

    def write(self, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            if self._size >= self._max_size:
                self._rotate()
            room = self._max_size - self._size
            written = os.write(self._fd, data[offset : offset + room])
            self._size += written
            offset += written

    def _rotate(self) -> None:
        os.close(self._fd)
        rotated_path(self._active, LOG_FILE_COUNT - 1).unlink(missing_ok=True)
        for index in range(LOG_FILE_COUNT - 2, 0, -1):
            src = rotated_path(self._active, index)
            if src.exists():
                src.rename(rotated_path(self._active, index + 1))
        self._active.rename(rotated_path(self._active, 1))
        self._fd = os.open(self._active, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        self._size = 0

    def close(self) -> None:
        os.close(self._fd)


def run(container_id: str, root: Path, max_total_bytes: int) -> int:
    sink = RotatingLog(root / f"{container_id}.log", max_total_bytes)

    # Only now. containerd holds the task in 'created' until this closes, so closing it earlier
    # would let the container start writing before we could take its output.
    os.close(_READY_FD)

    selector = selectors.DefaultSelector()
    for fd in (_STDOUT_FD, _STDERR_FD):
        selector.register(fd, selectors.EVENT_READ)
    open_fds = {_STDOUT_FD, _STDERR_FD}
    try:
        while open_fds:
            for key, _ in selector.select():
                fd = key.fd
                data = os.read(fd, _READ_SIZE)
                if not data:  # EOF: the container closed this stream
                    selector.unregister(fd)
                    os.close(fd)
                    open_fds.discard(fd)
                    continue
                sink.write(data)
    finally:
        sink.close()
        selector.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="containerd binary:// log writer")
    parser.add_argument("--log-root", required=True, type=Path)
    parser.add_argument("--max-length", required=True, type=int)
    # containerd flattens the URI's query into argv; ignore anything we do not know rather than
    # failing to start, which would take the container down with us.
    args, _unknown = parser.parse_known_args()

    container_id = os.environ.get("CONTAINER_ID")
    if not container_id:
        # No logging stack here by design (see the module docstring); stderr is what the shim
        # surfaces when a log binary fails to start.
        sys.stderr.write("CONTAINER_ID is not set; the shim did not invoke us\n")
        return 2
    return run(container_id, args.log_root, args.max_length)


if __name__ == "__main__":
    sys.exit(main())
