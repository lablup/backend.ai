"""Docker's half of the two-phase start gate, using :mod:`ai.backend.agent.gate`.

The entrypoint parks at a FIFO once its namespaces exist; the agent attaches to that PID, then
releases the wrapper to ``exec`` the real command in place. Docker's wrapper only waits.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, Final

from ai.backend.agent.errors.agent import ContainerStartupFailedError
from ai.backend.agent.gate import (
    GATE_MNT,
    GO_FIFO,
    PAUSE_SCRIPT_NAME,
    READY_MARKER,
    signal_go,
    write_gate,
)
from ai.backend.logging.structured import StructuredLogger

__all__ = (
    "GATE_WRAPPER",
    "apply_gate",
    "release_gate",
    "stage_gate",
    "wait_gated_pid",
)

log = StructuredLogger(logging.getLogger(__spec__.name))

#: How long to wait for the wrapper to park; longer means the entrypoint died or never started.
GATE_READY_TIMEOUT_SEC: Final = 30.0

GATE_WRAPPER: Final = f"""#!/bin/sh
: > {GATE_MNT}/{READY_MARKER}
read _ < {GATE_MNT}/{GO_FIFO} 2>/dev/null
exec "$@"
"""


def stage_gate(gate_dir: Path) -> None:
    """Write the wrapper and the FIFO for one container.

    No chown: Docker runs the entrypoint as real root on the host.
    """
    write_gate(gate_dir, GATE_WRAPPER, uid=os.geteuid(), gid=os.getegid())


def apply_gate(
    container_config: MutableMapping[str, Any], gate_dir: Path
) -> MutableMapping[str, Any]:
    """Point the container's entrypoint at the gate and bind the gate directory in.

    Mutates and returns ``container_config``. The existing entrypoint is kept after the wrapper,
    under whichever of ``EntryPoint``/``Entrypoint`` is in use; ``Cmd`` is untouched.
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
    """Block until the wrapper has parked in its final namespaces, then return the PID to attach to.

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
    """Let the wrapper exec the real command. Never blocks on a gate nothing is parked at."""
    if not signal_go(gate_dir):
        log.debug("gate release skipped, nothing parked", gate_dir=str(gate_dir))
