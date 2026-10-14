"""The two-phase start gate: hold a container in its own netns until the agent has attached.

A wrapper writes a ``ready`` marker, blocks on a FIFO, then ``exec``s the real command in place.
Shared here: mount point, marker, FIFO and ownership; wrapper bodies are per runtime.
"""

from __future__ import annotations

import asyncio
import errno
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Final

from ai.backend.agent.errors.agent import ContainerStartupFailedError

#: Where the gate directory is bind-mounted inside the container.
GATE_MNT: Final = "/.bai-gate"
#: Written by the wrapper once it is parked in the container's namespaces.
READY_MARKER: Final = "ready"
#: Read by the wrapper; writing to it releases the gate.
GO_FIFO: Final = "go"
#: The wrapper script, as the container sees it.
PAUSE_SCRIPT_NAME: Final = "pause.sh"

#: How long a release waits for the wrapper's reader. Bounded: on failure paths none is coming.
GATE_RELEASE_TIMEOUT_SEC: Final = 5.0
_GATE_RELEASE_POLL_SEC: Final = 0.05


def write_gate(gate_dir: Path, script_body: str, *, uid: int, gid: int) -> Path:
    """Stage the wrapper and the FIFO, owned by the uid the container runs as.

    The gate and its bind-mounted parent are chowned to that uid unless the agent runs as it.
    """
    gate_dir.mkdir(parents=True, exist_ok=True)
    script = gate_dir / PAUSE_SCRIPT_NAME
    script.write_text(script_body)
    script.chmod(0o755)
    fifo = gate_dir / GO_FIFO
    if not fifo.exists():
        os.mkfifo(fifo, 0o600)
    if os.geteuid() != uid:
        for path in (gate_dir.parent, gate_dir, script, fifo):
            os.chown(path, uid, gid)
    return script


def signal_go(gate_dir: Path, *, timeout_sec: float = GATE_RELEASE_TIMEOUT_SEC) -> bool:
    """Release the gate. Returns whether a reader was there to take it.

    Non-blocking and bounded: a blocking open would park an executor thread when no reader comes.
    Retries briefly because the marker is written before the wrapper opens the FIFO.
    """
    fifo = gate_dir / GO_FIFO
    deadline = time.monotonic() + timeout_sec
    while True:
        try:
            fd = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
        except FileNotFoundError:
            return False  # never created, or already cleaned up: nothing parks on it
        except OSError as e:
            if e.errno != errno.ENXIO:
                raise
            # ENXIO: no reader yet, the normal state of a container that never reached the gate.
            if time.monotonic() >= deadline:
                return False
            time.sleep(_GATE_RELEASE_POLL_SEC)
            continue
        with os.fdopen(fd, "w") as f:
            f.write("go\n")
        return True


async def wait_ready(
    gate_dir: Path,
    *,
    failure: Callable[[], str | None],
    poll_interval_sec: float = 0.1,
) -> None:
    """Block until the wrapper is parked in the container's final namespaces, or the launch died.

    ``failure`` returns a message once the launch is known dead. Unbounded: the caller owns the
    timeout.
    """
    ready = gate_dir / READY_MARKER
    while not ready.exists():
        if (reason := failure()) is not None:
            raise ContainerStartupFailedError(reason)
        await asyncio.sleep(poll_interval_sec)
