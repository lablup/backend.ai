from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.types import ContainerLifecycleEvent, LifecycleEvent
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
    @pytest.mark.parametrize(("current", "handled"), [(True, True), (False, False)])
    async def test_report_of_a_superseded_attempt_is_dropped(
        self, current: bool, handled: bool
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        attempt = object()
        agent = MagicMock()
        agent.kernel_registry = {}
        agent._ongoing_destruction_tasks = {}
        agent.registry_lock = AsyncMock()
        agent.reconstruct_resource_usage = AsyncMock()
        agent.anycast_and_broadcast_event = AsyncMock()
        agent.create_attempts = {kernel_id: attempt if current else object()}

        await AbstractAgent._handle_destroy_event(
            agent,
            ContainerLifecycleEvent(
                kernel_id,
                SessionId(uuid.uuid4()),
                None,
                LifecycleEvent.DESTROY,
                KernelLifecycleEventReason.FAILED_TO_CREATE,
                create_attempt=attempt,
            ),
        )

        assert (agent.anycast_and_broadcast_event.await_count == 1) is handled
        assert (kernel_id in agent.create_attempts) is not current
