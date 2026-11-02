"""Only a containerd task exit status reaches the kernel terminated events; Docker keeps -1."""

from __future__ import annotations

import asyncio
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import ContainerLifecycleEvent, LifecycleEvent
from ai.backend.common.events.event_types.kernel.anycast import KernelTerminatedAnycastEvent
from ai.backend.common.events.event_types.kernel.broadcast import KernelTerminatedBroadcastEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import ContainerId, KernelId, SessionId


@pytest.fixture
def agent() -> MagicMock:
    agent = MagicMock()
    agent._ongoing_destruction_tasks = {}
    agent.restarting_kernels = {}
    agent.kernel_registry = {}
    agent.registry_lock = asyncio.Lock()
    agent.stat_ctx.remove_kernel_metric = AsyncMock()
    agent.destroy_kernel = AsyncMock()
    agent.clean_kernel = AsyncMock()
    agent.reconstruct_resource_usage = AsyncMock()
    agent.anycast_and_broadcast_event = AsyncMock()
    agent.container_lifecycle_queue = asyncio.Queue()
    return agent


def _event(
    event: LifecycleEvent,
    *,
    exit_code: int | None = None,
    task_exit_status: int | None = None,
) -> ContainerLifecycleEvent:
    return ContainerLifecycleEvent(
        KernelId(uuid4()),
        SessionId(uuid4()),
        ContainerId("c0ffee"),
        event,
        KernelLifecycleEventReason.FAILED_TO_START,
        exit_code=exit_code,
        task_exit_status=task_exit_status,
    )


async def _terminated_exit_codes(agent: MagicMock, ev: ContainerLifecycleEvent) -> tuple[int, int]:
    await AbstractAgent._handle_clean_event(cast(Any, agent), ev)
    anycast, broadcast = agent.anycast_and_broadcast_event.await_args.args
    assert isinstance(anycast, KernelTerminatedAnycastEvent)
    assert isinstance(broadcast, KernelTerminatedBroadcastEvent)
    return anycast.exit_code, broadcast.exit_code


class TestHandleCleanEvent:
    async def test_containerd_task_exit_status_is_forwarded(self, agent: MagicMock) -> None:
        ev = _event(LifecycleEvent.CLEAN, task_exit_status=137)

        assert await _terminated_exit_codes(agent, ev) == (137, 137)

    async def test_docker_die_exit_code_is_not_forwarded(self, agent: MagicMock) -> None:
        # docker/agent.py passes the die event's raw exitCode attribute.
        ev = _event(LifecycleEvent.CLEAN, exit_code=cast(Any, "137"))

        assert await _terminated_exit_codes(agent, ev) == (-1, -1)


class TestHandleDestroyEvent:
    async def test_clean_event_inherits_the_task_exit_status(self, agent: MagicMock) -> None:
        ev = _event(LifecycleEvent.DESTROY, task_exit_status=137)
        agent.kernel_registry = {ev.kernel_id: MagicMock(state=None, runner=None)}

        await AbstractAgent._handle_destroy_event(cast(Any, agent), ev)

        clean = agent.container_lifecycle_queue.get_nowait()
        assert clean.event == LifecycleEvent.CLEAN
        assert clean.task_exit_status == 137
