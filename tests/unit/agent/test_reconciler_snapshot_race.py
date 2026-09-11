"""
Tests for the snapshot race both of the agent's periodic reconcilers can hit.

Each reads the container listing first and the kernel registry second. A kernel whose container
starts in between is absent from the listing while the start event has already marked it RUNNING,
so the set difference names a live kernel. Acting on that unregisters it, and the lifecycle sync
then destroys the container of a kernel it no longer knows.
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


def _running_container(session_id: SessionId) -> Container:
    return Container(
        id=ContainerId(f"container-{uuid4().hex[:12]}"),
        status=ContainerStatus.RUNNING,
        image="python:3.8",
        labels={LabelName.SESSION_ID: str(session_id)},
        ports=[],
        backend_obj=None,
    )


def _running_kernel(session_id: SessionId) -> MagicMock:
    kernel_obj = MagicMock()
    kernel_obj.session_id = session_id
    kernel_obj.state = KernelLifecycleStatus.RUNNING
    kernel_obj.container_id = None
    return kernel_obj


def _make_agent(
    *,
    listings: list[list[tuple[KernelId, Container]]],
    kernel_registry: dict[KernelId, MagicMock],
    active_creates: dict[KernelId, Any] | None = None,
) -> Any:
    """A stub carrying only what the reconcilers touch.

    `listings` is consumed one call at a time so a test can make the second listing differ from
    the first, which is exactly what the re-check is for.
    """
    agent = MagicMock()
    agent.id = AgentId("test-agent")
    agent.registry_lock = asyncio.Lock()
    agent.restarting_kernels = {}
    agent._active_creates = active_creates if active_creates is not None else {}
    agent.kernel_registry = kernel_registry
    agent.container_lifecycle_queue = asyncio.Queue()
    agent.set_container_count = AsyncMock()
    agent.produce_error_event = AsyncMock()

    remaining = list(listings)

    async def _enumerate(*args: Any, **kwargs: Any) -> list[tuple[KernelId, Container]]:
        listing = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        agent.on_listing()
        return listing

    agent.on_listing = MagicMock()
    agent.enumerate_containers = AsyncMock(side_effect=_enumerate)
    agent._is_reconcilable = lambda kid: AbstractAgent._is_reconcilable(agent, kid)
    agent._confirm_kernels_have_no_container = (
        lambda candidates: AbstractAgent._confirm_kernels_have_no_container(agent, candidates)
    )
    agent._report_kernels_whose_container_is_gone = (
        lambda candidates, session_map: AbstractAgent._report_kernels_whose_container_is_gone(
            agent, candidates, session_map
        )
    )
    return agent


def _drain(queue: asyncio.Queue[ContainerLifecycleEvent]) -> list[ContainerLifecycleEvent]:
    events: list[ContainerLifecycleEvent] = []
    while not queue.empty():
        events.append(queue.get_nowait())
    return events


async def _run_one_sweep(agent: Any) -> set[KernelId]:
    """One pass of `_clean_kernel_registry_loop`, without waiting out its 60s sleep."""
    cleaned: set[KernelId] = set()

    async def _clean(kernels: Any) -> None:
        cleaned.update(kernels)

    agent.clean_kernel_objects = AsyncMock(side_effect=_clean)
    task = asyncio.create_task(AbstractAgent._clean_kernel_registry_loop(agent))
    for _ in range(20):
        await asyncio.sleep(0)
        if agent.clean_kernel_objects.await_count or agent.enumerate_containers.await_count > 1:
            break
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    return cleaned


class TestDanglingSweep:
    async def test_a_kernel_still_being_created_is_not_swept(self) -> None:
        """The kernel is RUNNING and missing from the listing, but its create has not returned."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            listings=[[]],
            kernel_registry={kernel_id: _running_kernel(session_id)},
            active_creates={kernel_id: MagicMock()},
        )

        assert await _run_one_sweep(agent) == set()

    async def test_a_kernel_that_appears_in_a_fresh_listing_is_not_swept(self) -> None:
        """The first listing predates the container; the second one sees it."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            listings=[[], [(kernel_id, _running_container(session_id))]],
            kernel_registry={kernel_id: _running_kernel(session_id)},
        )

        assert await _run_one_sweep(agent) == set()

    async def test_a_kernel_absent_from_both_listings_is_swept(self) -> None:
        """The real dangling case still gets cleaned."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            listings=[[], []],
            kernel_registry={kernel_id: _running_kernel(session_id)},
        )

        assert await _run_one_sweep(agent) == {kernel_id}

    async def test_a_restarting_kernel_is_not_swept(self) -> None:
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            listings=[[], []],
            kernel_registry={kernel_id: _running_kernel(session_id)},
        )
        agent.restarting_kernels = {kernel_id: MagicMock()}

        assert await _run_one_sweep(agent) == set()


class TestLifecycleSync:
    async def test_a_kernel_still_being_created_is_not_reported_gone(self) -> None:
        """Same race, the 10s reconciler: its listing is taken before it takes the lock."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            listings=[[]],
            kernel_registry={kernel_id: _running_kernel(session_id)},
            active_creates={kernel_id: MagicMock()},
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        assert _drain(agent.container_lifecycle_queue) == []

    async def test_a_settled_kernel_with_no_container_is_still_reported(self) -> None:
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            listings=[[]],
            kernel_registry={kernel_id: _running_kernel(session_id)},
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        events = _drain(agent.container_lifecycle_queue)
        assert len(events) == 1
        assert events[0].kernel_id == kernel_id


class TestCleanKernelObject:
    async def test_the_entry_is_dropped_when_it_is_the_object_that_was_closed(self) -> None:
        kernel_id = KernelId(uuid4())
        kernel_obj = _running_kernel(SessionId(uuid4()))
        kernel_obj.runner = None
        kernel_obj.close = AsyncMock()
        kernel_obj.get = MagicMock(return_value=None)
        agent = _make_agent(listings=[[]], kernel_registry={kernel_id: kernel_obj})

        await AbstractAgent._clean_kernel_object(agent, kernel_id)

        assert kernel_id not in agent.kernel_registry

    async def test_a_replacement_object_is_left_alone(self) -> None:
        """A restart can put a new kernel object under the same id while `close()` awaits."""
        kernel_id = KernelId(uuid4())
        replacement = _running_kernel(SessionId(uuid4()))
        kernel_obj = _running_kernel(SessionId(uuid4()))
        kernel_obj.runner = None
        kernel_obj.get = MagicMock(return_value=None)
        agent = _make_agent(listings=[[]], kernel_registry={kernel_id: kernel_obj})

        async def _close() -> None:
            agent.kernel_registry[kernel_id] = replacement

        kernel_obj.close = AsyncMock(side_effect=_close)

        await AbstractAgent._clean_kernel_object(agent, kernel_id)

        assert agent.kernel_registry[kernel_id] is replacement

    async def test_an_absent_kernel_is_not_an_error(self) -> None:
        agent = _make_agent(listings=[[]], kernel_registry={})

        await AbstractAgent._clean_kernel_object(agent, KernelId(uuid4()))


@pytest.mark.parametrize("in_flight", ["_active_creates", "restarting_kernels"])
async def test_is_reconcilable_refuses_kernels_in_flight(in_flight: str) -> None:
    kernel_id = KernelId(uuid4())
    agent = _make_agent(listings=[[]], kernel_registry={})
    setattr(agent, in_flight, {kernel_id: MagicMock()})

    assert not AbstractAgent._is_reconcilable(agent, kernel_id)
    assert AbstractAgent._is_reconcilable(agent, KernelId(uuid4()))


class TestLifecycleSyncConfirmsBeforeCleaning:
    async def test_a_create_that_finishes_during_the_listing_is_not_cleaned(self) -> None:
        """The review's interleaving: the create leaves `_active_creates` before the comparison.

        The CLEAN this would raise removes the container with `force=True`, so the guard cannot
        rest on the older listing alone.
        """
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        active_creates: dict[KernelId, Any] = {kernel_id: MagicMock()}
        agent = _make_agent(
            listings=[[], [(kernel_id, _running_container(session_id))]],
            kernel_registry={kernel_id: _running_kernel(session_id)},
            active_creates=active_creates,
        )
        # The create completes while the first listing is being taken.
        agent.on_listing = MagicMock(side_effect=lambda: active_creates.pop(kernel_id, None))

        await AbstractAgent.sync_container_lifecycles(agent)

        assert _drain(agent.container_lifecycle_queue) == []

    async def test_a_kernel_replaced_between_the_listings_is_left_alone(self) -> None:
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        registry = {kernel_id: _running_kernel(session_id)}
        agent = _make_agent(listings=[[], []], kernel_registry=registry)
        calls: list[int] = []

        def _replace_after_first_listing() -> None:
            calls.append(1)
            if len(calls) == 2:
                registry[kernel_id] = _running_kernel(session_id)

        agent.on_listing = MagicMock(side_effect=_replace_after_first_listing)

        await AbstractAgent.sync_container_lifecycles(agent)

        assert _drain(agent.container_lifecycle_queue) == []

    async def test_a_kernel_gone_from_both_listings_is_still_cleaned(self) -> None:
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent(
            listings=[[], []],
            kernel_registry={kernel_id: _running_kernel(session_id)},
        )

        await AbstractAgent.sync_container_lifecycles(agent)

        events = _drain(agent.container_lifecycle_queue)
        assert len(events) == 1
        assert events[0].kernel_id == kernel_id
        assert events[0].event == LifecycleEvent.CLEAN
        assert events[0].reason == KernelLifecycleEventReason.CONTAINER_NOT_FOUND


class TestCleanupStartsOnTheObjectItJudged:
    async def test_an_id_reused_before_the_cleanup_task_runs_is_left_alone(self) -> None:
        """The sweep judged one object; another is under the id by the time cleanup starts."""
        kernel_id = KernelId(uuid4())
        judged = _running_kernel(SessionId(uuid4()))
        judged.runner = None
        judged.close = AsyncMock()
        judged.get = MagicMock(return_value=None)
        replacement = _running_kernel(SessionId(uuid4()))
        replacement.close = AsyncMock()
        agent = _make_agent(listings=[[]], kernel_registry={kernel_id: replacement})

        await AbstractAgent._clean_kernel_object(agent, kernel_id, judged)

        assert agent.kernel_registry[kernel_id] is replacement
        replacement.close.assert_not_awaited()
        judged.close.assert_not_awaited()

    async def test_a_kernel_that_re_entered_creation_is_left_alone(self) -> None:
        kernel_id = KernelId(uuid4())
        kernel_obj = _running_kernel(SessionId(uuid4()))
        kernel_obj.runner = None
        kernel_obj.close = AsyncMock()
        kernel_obj.get = MagicMock(return_value=None)
        agent = _make_agent(
            listings=[[]],
            kernel_registry={kernel_id: kernel_obj},
            active_creates={kernel_id: MagicMock()},
        )

        await AbstractAgent._clean_kernel_object(agent, kernel_id, kernel_obj)

        kernel_obj.close.assert_not_awaited()
        assert kernel_id in agent.kernel_registry
