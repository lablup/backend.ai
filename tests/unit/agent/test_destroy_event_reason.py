from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import ContainerLifecycleEvent, CreationAttempt, LifecycleEvent
from ai.backend.common.events.event_types.kernel.anycast import KernelTerminatedAnycastEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import KernelId, SessionId


class TestHandleDestroyEventForMissingKernel:
    @pytest.mark.parametrize(
        ("reason", "expected"),
        [
            (
                KernelLifecycleEventReason.FAILED_TO_CREATE,
                KernelLifecycleEventReason.FAILED_TO_CREATE,
            ),
            (
                KernelLifecycleEventReason.USER_REQUESTED,
                KernelLifecycleEventReason.ALREADY_TERMINATED,
            ),
        ],
    )
    async def test_terminated_reason(
        self,
        reason: KernelLifecycleEventReason,
        expected: KernelLifecycleEventReason,
    ) -> None:
        agent = MagicMock()
        agent.kernel_registry = {}
        agent._ongoing_destruction_tasks = {}
        agent.registry_lock = AsyncMock()
        agent.reconstruct_resource_usage = AsyncMock()
        agent.anycast_and_broadcast_event = AsyncMock()
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        await AbstractAgent._handle_destroy_event(
            agent,
            ContainerLifecycleEvent(kernel_id, session_id, None, LifecycleEvent.DESTROY, reason),
        )

        agent.anycast_and_broadcast_event.assert_awaited_once()
        anycast = agent.anycast_and_broadcast_event.await_args.args[0]
        assert isinstance(anycast, KernelTerminatedAnycastEvent)
        assert anycast.kernel_id == kernel_id
        assert anycast.reason == expected


class TestHandleDestroyEventForStaleCreationFailure:
    @pytest.fixture
    def agent(self) -> MagicMock:
        agent = MagicMock()
        agent.kernel_registry = {}
        agent._ongoing_destruction_tasks = {}
        agent.registry_lock = asyncio.Lock()
        agent.reconstruct_resource_usage = AsyncMock()
        agent.anycast_and_broadcast_event = AsyncMock()
        agent.destroy_kernel = AsyncMock()
        agent.container_lifecycle_queue = asyncio.Queue()
        agent.create_attempts = {}
        return agent

    def _report(self, kernel_id: KernelId, attempt: CreationAttempt) -> ContainerLifecycleEvent:
        return ContainerLifecycleEvent(
            kernel_id,
            SessionId(uuid.uuid4()),
            None,
            LifecycleEvent.DESTROY,
            KernelLifecycleEventReason.FAILED_TO_CREATE,
            create_attempt=attempt,
        )

    async def test_report_of_a_superseded_attempt_spares_the_retried_kernel(
        self, agent: MagicMock
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        stale, retry = CreationAttempt(), CreationAttempt()
        retried_kernel = MagicMock()
        agent.kernel_registry = {kernel_id: retried_kernel}
        agent.create_attempts = {kernel_id: retry}

        await AbstractAgent._handle_destroy_event(agent, self._report(kernel_id, stale))

        agent.destroy_kernel.assert_not_awaited()
        agent.anycast_and_broadcast_event.assert_not_awaited()
        assert agent.kernel_registry == {kernel_id: retried_kernel}
        assert agent.create_attempts == {kernel_id: retry}

    async def test_report_of_the_current_attempt_is_handled_once(self, agent: MagicMock) -> None:
        kernel_id = KernelId(uuid.uuid4())
        attempt = CreationAttempt()
        agent.create_attempts = {kernel_id: attempt}

        await AbstractAgent._handle_destroy_event(agent, self._report(kernel_id, attempt))

        agent.anycast_and_broadcast_event.assert_awaited_once()
        assert kernel_id not in agent.create_attempts
