"""Start, stop and remove kernel containers through the containerd API."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Mapping, Sequence
from typing import Any, Final

from ai.backend.agent.containerd.client import (
    ContainerdAPI,
    ContainerRecord,
    MountSpec,
    TaskInfo,
    TaskState,
)
from ai.backend.agent.errors.containerd import ContainerdOperationFailed
from ai.backend.common.exception import BackendAIError
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

STOP_GRACE_SEC: Final = 10.0
KILL_WAIT_SEC: Final = 10.0
_POLL_SEC: Final = 0.1
_GONE: Final = frozenset({TaskState.STOPPED, TaskState.CREATED, TaskState.UNKNOWN})


def is_gone(task: TaskInfo | None) -> bool:
    """True when no process of the task is running."""
    return task is None or task.state in _GONE


async def _wait_gone(client: ContainerdAPI, container_id: str, timeout_sec: float) -> bool:
    deadline = asyncio.get_running_loop().time() + timeout_sec
    while True:
        if is_gone(await client.get_task(container_id)):
            return True
        if asyncio.get_running_loop().time() >= deadline:
            return False
        await asyncio.sleep(_POLL_SEC)


async def launch_container(
    client: ContainerdAPI,
    record: ContainerRecord,
    *,
    runtime: str,
    chain_id: str,
    spec: Mapping[str, Any],
    stdio: str,
) -> int:
    """Prepare the rootfs snapshot, create the container and start its task; returns the PID.

    Whatever was created is removed again when a step fails.
    """
    rootfs: Sequence[MountSpec] = await client.prepare_snapshot(record.snapshot_key, chain_id)
    try:
        await client.create_container(record, runtime, spec)
        pid = await client.create_task(record.id, rootfs, stdio, stdio)
        await client.start_task(record.id)
    except BaseException:
        try:
            await clean_container(client, record.id)
        except BackendAIError:
            log.exception("cleanup after a failed launch failed", container_id=record.id)
        raise
    return pid


async def destroy_container(
    client: ContainerdAPI,
    container_id: str,
    *,
    grace_sec: float = STOP_GRACE_SEC,
) -> bool:
    """Stop the task: SIGINT, then SIGKILL after the grace period. False if nothing was found."""
    task = await client.get_task(container_id)
    if task is None:
        return await client.get_container(container_id) is not None
    if not is_gone(task):
        await client.kill_task(container_id, signal.SIGINT, all_processes=False)
        if not await _wait_gone(client, container_id, grace_sec):
            await client.kill_task(container_id, signal.SIGKILL, all_processes=True)
            if not await _wait_gone(client, container_id, KILL_WAIT_SEC):
                raise ContainerdOperationFailed(
                    f"the task of {container_id} did not exit after SIGKILL"
                )
    await client.delete_task(container_id)
    return True


async def clean_container(client: ContainerdAPI, container_id: str) -> None:
    """Remove the task, the container record and the rootfs snapshot; missing pieces are skipped."""
    record = await client.get_container(container_id)
    task = await client.get_task(container_id)
    if task is not None:
        if not is_gone(task):
            await client.kill_task(container_id, signal.SIGKILL, all_processes=True)
            await _wait_gone(client, container_id, KILL_WAIT_SEC)
        await client.delete_task(container_id)
    await client.delete_container(container_id)
    await client.remove_snapshot(record.snapshot_key if record is not None else container_id)
