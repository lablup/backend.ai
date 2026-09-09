"""Docker's half of the two-phase start gate (BEP-1078).

The network has to be attached while the container's netns exists and its PID is stable, but before
the user's command runs -- attaching afterwards races krunner's network-dependent init (REPL bind,
SSH, peer lookup). containerd splits ``create task`` from ``start task`` and gives that for free.
Docker does not: ``docker create`` yields ``State.Pid == 0`` and no netns at all, and ``docker
start`` creates the netns and execs the command in one step.

So Docker uses the same wrapper the rootless backends use (:mod:`ai.backend.agent.gate`): the
container's entrypoint parks at a FIFO after its namespaces exist, the agent attaches to the PID it
finds there, and releasing the FIFO lets the wrapper ``exec`` the real command in place.

Measured on Docker 29.1.3: while gated the container holds two interfaces (``lo``, ``tunl0``) and
has not run its command; a veth moved in raises that to three; after release the PID is unchanged
and the command sees the interface. That "PID is unchanged" is the property the whole arrangement
exists for -- it is why the agent may attach to a PID before knowing what will run there.

Docker applies its own seccomp profile and IPC namespace, so the wrapper only waits; compare the
rootless base, whose wrapper has to install a seccomp filter before the exec.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Final

from ai.backend.agent.errors.agent import ContainerStartupFailedError
from ai.backend.agent.gate import GATE_MNT, GO_FIFO, PAUSE_SCRIPT_NAME, READY_MARKER, write_gate

__all__ = (
    "GATE_WRAPPER",
    "apply_gate",
    "release_gate",
    "stage_gate",
    "wait_gated_pid",
)

#: How long to wait for the wrapper to park. It only has to write one file after Docker has set up
#: its namespaces; longer than this means the container died or never started the entrypoint.
GATE_READY_TIMEOUT_SEC: Final = 30.0

GATE_WRAPPER: Final = f"""#!/bin/sh
: > {GATE_MNT}/{READY_MARKER}
read _ < {GATE_MNT}/{GO_FIFO} 2>/dev/null
exec "$@"
"""


def stage_gate(gate_dir: Path) -> None:
    """Write the wrapper and the FIFO for one container.

    Unlike the rootless backends, nothing is handed over: Docker runs the container's entrypoint as
    real root on the host, so it reads and writes the agent's own files whatever they are owned by.
    The rootless gate has to chown because its container is *not* root out here.
    """
    write_gate(gate_dir, GATE_WRAPPER, uid=os.geteuid(), gid=os.getegid())


def apply_gate(
    container_config: MutableMapping[str, Any], gate_dir: Path
) -> MutableMapping[str, Any]:
    """Point the container's entrypoint at the gate and bind the gate directory in.

    Mutates and returns ``container_config`` -- the same dict the Docker backend has been building
    all along, so this stays one step in that path rather than a second way to describe a container.

    The entrypoint already in the config is kept and placed *after* the wrapper. Docker hands
    Entrypoint+Cmd to the first element, so replacing Entrypoint outright drops whatever was there
    -- and for a Backend.AI kernel that is `/opt/kernel/entrypoint.sh`, which sets the container up
    (uid/gid, ssh keys, the bootstrap script) before the runner starts. Measured on a gated
    container: the runner ran directly as root and logged "/home/work (uid: 1000) is not owned by
    the current user 0", with none of the entrypoint's own output, and the kernel never answered
    the agent's service-app handshake.

    Both spellings are read because the Docker backend writes ``EntryPoint`` while the API field is
    ``Entrypoint``; the wrapper is written back under the spelling that was already in use, so this
    adds no second source of truth. ``Cmd`` is left exactly as it was.
    """
    key = "EntryPoint" if "EntryPoint" in container_config else "Entrypoint"
    existing = container_config.get(key) or []
    inherited = [str(part) for part in existing if str(part)]
    container_config[key] = [f"{GATE_MNT}/{PAUSE_SCRIPT_NAME}", *inherited]
    host_config = container_config.setdefault("HostConfig", {})
    binds = host_config.setdefault("Binds", [])
    binds.append(f"{gate_dir}:{GATE_MNT}:rw")
    return container_config


async def wait_gated_pid(
    container: Any,
    gate_dir: Path,
    *,
    timeout_sec: float = GATE_READY_TIMEOUT_SEC,
) -> int:
    """Block until the wrapper has parked, then return the PID to attach to.

    Waiting for the marker rather than for ``start()`` to return is the point: the marker is written
    from inside the final namespaces, by the process that is still there after the exec. A PID read
    before that could be a setup process that will not survive.

    Raises ``TimeoutError`` if the wrapper never parks and a domain error if startup fails.
    """
    ready = gate_dir / READY_MARKER

    async def _failed() -> str | None:
        state = (await container.show()).get("State") or {}
        if state.get("Running"):
            return None
        return (
            f"container exited before reaching the gate "
            f"(status={state.get('Status')!r}, exit={state.get('ExitCode')!r})"
        )

    async with asyncio.timeout(timeout_sec):
        while not ready.exists():
            if (reason := await _failed()) is not None:
                raise ContainerStartupFailedError(reason)
            await asyncio.sleep(0.1)
    pid = int(((await container.show()).get("State") or {}).get("Pid") or 0)
    if pid <= 0:
        raise ContainerStartupFailedError("the container parked at the gate but reports no PID")
    return pid


def release_gate(gate_dir: Path) -> None:
    """Let the wrapper exec the real command. Blocks only as long as the write takes: the reader is
    already parked, which is what the ready marker attested."""
    with (gate_dir / GO_FIFO).open("w") as f:
        f.write("go\n")
