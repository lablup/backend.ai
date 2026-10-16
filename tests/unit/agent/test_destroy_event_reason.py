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
