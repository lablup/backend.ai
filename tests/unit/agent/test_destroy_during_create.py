"""
Tests for a destroy that arrives while ``AbstractAgent.create_kernel()`` is still running.

The destroy cancels the creation, waits until it has unwound, and only then reports the
termination, so no container comes up after the kernel is reported as destroyed.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.agent import AbstractAgent, CreateTaskInfo
from ai.backend.agent.types import (
    CREATION_DESTROYED_MESSAGE,
    ContainerLifecycleEvent,
    LifecycleEvent,
)
from ai.backend.common.events.event_types.kernel.anycast import KernelTerminatedAnycastEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import ContainerId, KernelId, SessionId


def _make_agent() -> Any:
    """A stub carrying only what the destroy handler touches."""
    agent = MagicMock()
    agent._active_creates = {}
    agent._pending_creation_tasks = defaultdict(set)
    agent._ongoing_destruction_tasks = {}
    agent.restarting_kernels = {}
    agent.registry_lock = asyncio.Lock()
    agent.kernel_registry = {}
    agent.clean_kernel = AsyncMock()
    agent.reconstruct_resource_usage = AsyncMock()
    agent.anycast_and_broadcast_event = AsyncMock()
    agent.produce_error_event = AsyncMock()

    async def cancel_ongoing_create(kernel_id: KernelId) -> bool:
        return await AbstractAgent._cancel_ongoing_create(agent, kernel_id)

    agent._cancel_ongoing_create = cancel_ongoing_create
    return agent


def _destroy_event(kernel_id: KernelId, session_id: SessionId) -> ContainerLifecycleEvent:
    return ContainerLifecycleEvent(
        kernel_id,
        session_id,
        None,
        LifecycleEvent.DESTROY,
        KernelLifecycleEventReason.USER_REQUESTED,
        done_future=asyncio.get_running_loop().create_future(),
    )


class TestDestroyDuringCreate:
    async def test_destroy_cancels_creation_and_cleans_up_after_it_unwound(self) -> None:
        """A destroy mid-create cancels the creation, then cleans what it left behind."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent()
        steps: list[str] = []
        creating = asyncio.Event()

        async def create() -> None:
            try:
                creating.set()
                await asyncio.sleep(3600)  # e.g. pulling the image
            except asyncio.CancelledError:
                steps.append("create-unwound")
                raise

        create_task = asyncio.create_task(create())
        create_info = CreateTaskInfo(kernel_id=kernel_id, session_id=session_id, task=create_task)
        agent._active_creates[kernel_id] = create_info
        agent.clean_kernel.side_effect = lambda *_: steps.append("clean")
        await creating.wait()

        ev = _destroy_event(kernel_id, session_id)
        await AbstractAgent._handle_destroy_event(agent, ev)

        assert create_task.cancelled()
        assert create_info.cancelled_by_destroy
        assert steps == ["create-unwound", "clean"]
        agent.clean_kernel.assert_awaited_once_with(kernel_id, None, False)
        anycast_event = agent.anycast_and_broadcast_event.await_args.args[0]
        assert isinstance(anycast_event, KernelTerminatedAnycastEvent)
        assert anycast_event.reason == KernelLifecycleEventReason.USER_REQUESTED
        assert ev.done_future is not None and ev.done_future.done()

    async def test_destroy_without_creation_keeps_already_terminated(self) -> None:
        """A destroy for a kernel nobody is creating is reported as already terminated."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent()

        await AbstractAgent._handle_destroy_event(agent, _destroy_event(kernel_id, session_id))

        agent.clean_kernel.assert_not_awaited()
        anycast_event = agent.anycast_and_broadcast_event.await_args.args[0]
        assert anycast_event.reason == KernelLifecycleEventReason.ALREADY_TERMINATED

    async def test_creation_in_readiness_polling_is_left_to_the_termination_report(self) -> None:
        """The readiness polling phase is cancelled by the termination event, not here."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent()
        create_task = asyncio.create_task(asyncio.sleep(3600))
        agent._active_creates[kernel_id] = CreateTaskInfo(
            kernel_id=kernel_id, session_id=session_id, task=create_task
        )
        agent._pending_creation_tasks[kernel_id].add(create_task)

        assert await AbstractAgent._cancel_ongoing_create(agent, kernel_id) is False
        assert not create_task.cancelled()
        create_task.cancel()

    async def test_cancellation_carries_the_destroy_message(self) -> None:
        """The create RPC tells the destroy's cancellation from a cancelled request by its message."""
        kernel_id = KernelId(uuid4())
        agent = _make_agent()

        async def create() -> None:
            await asyncio.shield(asyncio.ensure_future(asyncio.sleep(3600)))

        create_task = asyncio.create_task(create())
        agent._active_creates[kernel_id] = CreateTaskInfo(
            kernel_id=kernel_id, session_id=SessionId(uuid4()), task=create_task
        )

        assert await AbstractAgent._cancel_ongoing_create(agent, kernel_id) is True

        with pytest.raises(asyncio.CancelledError) as exc_info:
            create_task.result()
        assert exc_info.value.args == (CREATION_DESTROYED_MESSAGE,)

    async def test_only_the_first_destroy_cancels_the_creation(self) -> None:
        """A second destroy waits for the unwinding but does not clean or report again."""
        kernel_id = KernelId(uuid4())
        agent = _make_agent()
        create_task = asyncio.create_task(asyncio.sleep(3600))
        agent._active_creates[kernel_id] = CreateTaskInfo(
            kernel_id=kernel_id, session_id=SessionId(uuid4()), task=create_task
        )

        first, second = await asyncio.gather(
            AbstractAgent._cancel_ongoing_create(agent, kernel_id),
            AbstractAgent._cancel_ongoing_create(agent, kernel_id),
        )

        assert (first, second) == (True, False)

    async def test_destroy_stops_the_container_recorded_by_the_cancelled_creation(self) -> None:
        """A container that came up before the creation unwound is destroyed by its id."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent()
        agent.destroy_kernel = AsyncMock()
        agent.container_lifecycle_queue = asyncio.Queue()
        kernel_obj = MagicMock()
        kernel_obj.container_id = ContainerId("c1")
        kernel_obj.runner = None

        async def create() -> None:
            try:
                await asyncio.sleep(3600)
            finally:
                agent.kernel_registry[kernel_id] = kernel_obj

        create_task = asyncio.create_task(create())
        agent._active_creates[kernel_id] = CreateTaskInfo(
            kernel_id=kernel_id, session_id=session_id, task=create_task
        )
        await asyncio.sleep(0)

        await AbstractAgent._handle_destroy_event(agent, _destroy_event(kernel_id, session_id))

        agent.destroy_kernel.assert_awaited_once_with(kernel_id, ContainerId("c1"))
        clean_event = agent.container_lifecycle_queue.get_nowait()
        assert clean_event.event == LifecycleEvent.CLEAN
        assert clean_event.container_id == ContainerId("c1")

    @pytest.mark.parametrize(
        "reason",
        [KernelLifecycleEventReason.FAILED_TO_CREATE, KernelLifecycleEventReason.FAILED_TO_START],
    )
    async def test_creation_failing_on_its_own_is_not_cancelled(
        self, reason: KernelLifecycleEventReason
    ) -> None:
        """The destroy that the failing creation injects lets it finish raising its own error."""
        kernel_id = KernelId(uuid4())
        session_id = SessionId(uuid4())
        agent = _make_agent()
        agent.container_lifecycle_queue = asyncio.Queue()
        create_task = asyncio.create_task(asyncio.sleep(3600))
        agent._active_creates[kernel_id] = CreateTaskInfo(
            kernel_id=kernel_id, session_id=session_id, task=create_task
        )

        await AbstractAgent.inject_container_lifecycle_event(
            agent, kernel_id, session_id, LifecycleEvent.DESTROY, reason
        )

        assert await AbstractAgent._cancel_ongoing_create(agent, kernel_id) is False
        assert not create_task.cancelled()
        create_task.cancel()

    async def test_restarting_kernel_creation_is_not_cancelled(self) -> None:
        """The restart waits for its creation, so a destroy leaves it to the restart."""
        kernel_id = KernelId(uuid4())
        agent = _make_agent()
        agent.restarting_kernels[kernel_id] = MagicMock()
        create_task = asyncio.create_task(asyncio.sleep(3600))
        agent._active_creates[kernel_id] = CreateTaskInfo(
            kernel_id=kernel_id, session_id=SessionId(uuid4()), task=create_task
        )

        assert await AbstractAgent._cancel_ongoing_create(agent, kernel_id) is False
        create_task.cancel()
