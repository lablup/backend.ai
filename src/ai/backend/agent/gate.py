"""The two-phase start gate: hold a container in its own netns until the agent has attached.

BEP-1079 needs a container whose network namespace exists and whose PID is stable *before* the
user's command runs, so a veth can be moved into it:

    handle = await runtime.create_task(cid)   # netns exists, user command NOT exec'd
    await network.attach(..., task_pid=handle.pid)
    await runtime.start_task(cid)             # release the gate -> exec

Only containerd offers that split natively. enroot, apptainer, podman and Docker all exec the
container's command the moment it starts -- ``docker create`` does not even give the container a
PID, let alone a netns. It is emulated the same way in all of them: the container's command is a
small wrapper that writes a ``ready`` marker, blocks reading a FIFO, then ``exec``s the real
command. Because it execs in place, the PID the agent attached to is the PID the user's process
ends up with. (Measured on Docker 29.1.3: gated PID and post-release PID are the same, and the
command sees the interface that was moved in while it waited.)

The wrapper's body is not shared. A runtime that applies neither a seccomp profile nor an IPC
namespace for us has the wrapper install those before the exec; podman and Docker do both
themselves, so their wrappers only wait. What is shared is the protocol -- the mount point, the
marker, the FIFO, and who owns them -- which is what lives here.
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

#: How long a release waits for the wrapper's reader before giving up. Bounded because the caller
#: releases from a `finally`, and on the failure paths no reader is ever coming.
GATE_RELEASE_TIMEOUT_SEC: Final = 5.0
_GATE_RELEASE_POLL_SEC: Final = 0.05


def write_gate(gate_dir: Path, script_body: str, *, uid: int, gid: int) -> Path:
    """Stage the wrapper and the FIFO, owned by the uid the container runs as.

    The container -- not the agent -- writes the ready marker and reads the FIFO, so the gate and
    its parent (the per-container state dir, which is what gets bind-mounted) must belong to the
    kernel uid. No-op when the agent already runs as that uid.
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

    Non-blocking and bounded, because a plain ``open("w")`` on a FIFO waits for a reader for as
    long as it takes -- and the callers release from a ``finally``, including the paths where the
    container exited before parking and no reader is ever coming. That call runs in a worker
    thread, so each one parked there is a thread lost from the default executor; a handful of bad
    image starts and every other `run_in_executor` in the agent stops with it.

    The brief retry is for the other side of the same race: the marker is written before the
    wrapper opens the FIFO, so a release that lands in between would see no reader yet.
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
            # ENXIO is the FIFO saying "no reader". Not an error here -- it is the normal state
            # of a container that never reached the gate.
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
    """Block until the wrapper is parked in the container's namespaces, or the launch died.

    Waiting for the marker rather than for "the runtime returned" is what keeps the attach off a
    transient setup PID: the marker is written from inside the final namespaces, by the process
    that will still be there after the exec.

    ``failure`` is polled between checks and returns a message once the launch is known to have
    died -- without it a container that failed immediately would be waited on for the caller's
    whole timeout and then reported as slow rather than as broken.

    Unbounded on purpose: the caller wraps this in ``asyncio.timeout`` so the deadline and the
    message that describes overrunning it stay with the backend that knows how to diagnose it.
    """
    ready = gate_dir / READY_MARKER
    while not ready.exists():
        if (reason := failure()) is not None:
            raise ContainerStartupFailedError(reason)
        await asyncio.sleep(poll_interval_sec)
