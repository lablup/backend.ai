"""
Tests for the registry-state guard in ``AbstractAgent.sync_container_lifecycles()``.

A kernel that is already being destroyed (its own destroy flow reports the real
termination reason) must not be re-reported as self-terminated just because its
container has already exited. Containers the agent no longer tracks — e.g. ones
it missed across a restart — must still be picked up.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import (
    Container,
    ContainerEnumerationResult,
    ContainerLifecycleEvent,
    KernelLifecycleStatus,
    LifecycleEvent,
)
from ai.backend.common.docker import LabelName
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    ContainerStatus,
    KernelId,
    SessionId,
)


def _dead_container(session_id: SessionId) -> Container:
    return Container(
        id=ContainerId(f"container-{uuid4().hex[:12]}"),
        status=ContainerStatus.EXITED,
        image="python:3.8",
        labels={LabelName.SESSION_ID: str(session_id)},
        ports=[],
        backend_obj=None,
    )


def _running_container(session_id: SessionId) -> Container:
    return Container(
        id=ContainerId(f"container-{uuid4().hex[:12]}"),
        status=ContainerStatus.RUNNING,
        image="python:3.8",
        labels={LabelName.SESSION_ID: str(session_id)},
        ports=[],
        backend_obj=None,
    )


def _tracked_kernel(session_id: SessionId, state: KernelLifecycleStatus) -> MagicMock:
    kernel_obj = MagicMock()
    kernel_obj.session_id = session_id
    kernel_obj.state = state
    kernel_obj.container_id = None
    return kernel_obj


def _make_agent(
    *,
    containers: list[tuple[KernelId, Container]],
    kernel_registry: dict[KernelId, MagicMock],
    complete: bool = True,
) -> Any:
    """A stub carrying only what ``sync_container_lifecycles()`` touches."""
    agent = MagicMock()
    agent.id = AgentId("test-agent")
    agent.enumerate_containers = AsyncMock(
        return_value=ContainerEnumerationResult(containers=containers, complete=complete)
    )
    agent.registry_lock = asyncio.Lock()
    agent.restarting_kernels = {}
    agent.kernel_registry = kernel_registry
    agent.container_lifecycle_queue = asyncio.Queue()
    agent.set_container_count = AsyncMock()
    agent.produce_error_event = AsyncMock()
    return agent


def _drain(queue: asyncio.Queue[ContainerLifecycleEvent]) -> list[ContainerLifecycleEvent]:
    events: list[ContainerLifecycleEvent] = []
    while not queue.empty():
        events.append(queue.get_nowait())
    return events


class TestSyncContainerLifecycles:
    async def test_untracked_dead_container_is_still_cleaned_up(self) -> None:
        """A dead container missing from the registry is still reported as self-terminated."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            containers=[(kernel_id, _dead_container(session_id))],
            kernel_registry={},
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        events = _drain(agent.container_lifecycle_queue)
        assert len(events) == 1
        assert events[0].kernel_id == kernel_id
        assert events[0].event == LifecycleEvent.CLEAN
        assert events[0].reason == KernelLifecycleEventReason.SELF_TERMINATED

    async def test_running_kernel_with_dead_container_is_cleaned_up(self) -> None:
        """A kernel the agent still believes is RUNNING is cleaned up as before."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            containers=[(kernel_id, _dead_container(session_id))],
            kernel_registry={kernel_id: _tracked_kernel(session_id, KernelLifecycleStatus.RUNNING)},
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        events = _drain(agent.container_lifecycle_queue)
        assert len(events) == 1
        assert events[0].kernel_id == kernel_id
        assert events[0].event == LifecycleEvent.CLEAN

    async def test_incomplete_listing_processes_present_containers(self) -> None:
        dead_kernel_id = KernelId(uuid4())
        active_kernel_id = KernelId(uuid4())
        agent = _make_agent(
            containers=[
                (dead_kernel_id, _dead_container(SessionId(uuid4()))),
                (active_kernel_id, _running_container(SessionId(uuid4()))),
            ],
            kernel_registry={},
            complete=False,
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        events = {event.kernel_id: event for event in _drain(agent.container_lifecycle_queue)}
        assert events[dead_kernel_id].event == LifecycleEvent.CLEAN
        assert events[active_kernel_id].event == LifecycleEvent.DESTROY
        agent.set_container_count.assert_awaited_once_with(1)
        agent.produce_error_event.assert_not_awaited()

    async def test_incomplete_listing_skips_missing_container_check(self) -> None:
        kernel_id = KernelId(uuid4())
        agent = _make_agent(
            containers=[],
            kernel_registry={
                kernel_id: _tracked_kernel(SessionId(uuid4()), KernelLifecycleStatus.RUNNING)
            },
            complete=False,
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        assert _drain(agent.container_lifecycle_queue) == []
        agent.set_container_count.assert_awaited_once_with(0)
        agent.produce_error_event.assert_not_awaited()

    @pytest.mark.parametrize(
        "state",
        [KernelLifecycleStatus.PREPARING, KernelLifecycleStatus.TERMINATING],
    )
    async def test_tracked_kernel_outside_running_is_skipped(
        self, state: KernelLifecycleStatus
    ) -> None:
        """A TERMINATING kernel whose container already exited keeps the reason its
        own destroy flow records, instead of being re-reported as self-terminated."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            containers=[(kernel_id, _dead_container(session_id))],
            kernel_registry={kernel_id: _tracked_kernel(session_id, state)},
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        agent.produce_error_event.assert_not_called()
        assert _drain(agent.container_lifecycle_queue) == []
