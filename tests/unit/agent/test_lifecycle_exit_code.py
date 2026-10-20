"""The exit code of a lifecycle event reaches the kernel terminated events."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
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
    agent.clean_kernel = AsyncMock()
    agent.reconstruct_resource_usage = AsyncMock()
    agent.anycast_and_broadcast_event = AsyncMock()
    return agent


def _clean_event(exit_code: int | None) -> ContainerLifecycleEvent:
    return ContainerLifecycleEvent(
        KernelId(uuid4()),
        SessionId(uuid4()),
        ContainerId("c0ffee"),
        LifecycleEvent.CLEAN,
        KernelLifecycleEventReason.FAILED_TO_START,
        exit_code=exit_code,
    )


async def _terminated_events(agent: MagicMock, ev: ContainerLifecycleEvent) -> Sequence[Any]:
    await AbstractAgent._handle_clean_event(cast(Any, agent), ev)
    return cast(Sequence[Any], agent.anycast_and_broadcast_event.await_args.args)


@pytest.mark.parametrize(("exit_code", "expected"), [(137, 137), (None, -1)])
async def test_clean_event_reports_the_exit_code(
    agent: MagicMock, exit_code: int | None, expected: int
) -> None:
    anycast, broadcast = await _terminated_events(agent, _clean_event(exit_code))

    assert isinstance(anycast, KernelTerminatedAnycastEvent)
    assert isinstance(broadcast, KernelTerminatedBroadcastEvent)
    assert anycast.exit_code == expected
    assert broadcast.exit_code == expected
    assert anycast.reason == KernelLifecycleEventReason.FAILED_TO_START
