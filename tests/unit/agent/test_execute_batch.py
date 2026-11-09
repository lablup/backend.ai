from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors import KernelNotFoundError
from ai.backend.common.events.event_types.kernel.anycast import KernelTerminatedAnycastEvent
from ai.backend.common.events.event_types.kernel.broadcast import KernelTerminatedBroadcastEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import KernelId, SessionId


@dataclass(frozen=True)
class _BatchRunWhoseKernelDisappears:
    agent: MagicMock
    session_id: SessionId
    kernel_id: KernelId


@pytest.fixture
def batch_run_whose_kernel_disappears() -> _BatchRunWhoseKernelDisappears:
    kernel_id = KernelId(uuid.uuid4())
    agent = MagicMock()
    agent.kernel_registry = {kernel_id: MagicMock()}
    agent.execute = AsyncMock(
        side_effect=KernelNotFoundError(
            f"The container for kernel {kernel_id} is not found (it might be terminated)."
        )
    )
    agent.anycast_and_broadcast_event = AsyncMock()
    return _BatchRunWhoseKernelDisappears(
        agent=agent,
        session_id=SessionId(uuid.uuid4()),
        kernel_id=kernel_id,
    )


class TestExecuteBatch:
    async def test_sends_kernel_terminated_events_when_the_kernel_disappears(
        self, batch_run_whose_kernel_disappears: _BatchRunWhoseKernelDisappears
    ) -> None:
        batch_run = batch_run_whose_kernel_disappears

        await AbstractAgent.execute_batch(
            cast(AbstractAgent[Any, Any], batch_run.agent),
            batch_run.session_id,
            batch_run.kernel_id,
            "sleep 3600",
        )

        batch_run.agent.anycast_and_broadcast_event.assert_awaited_once_with(
            KernelTerminatedAnycastEvent(
                kernel_id=batch_run.kernel_id,
                session_id=batch_run.session_id,
                reason=KernelLifecycleEventReason.SELF_TERMINATED,
            ),
            KernelTerminatedBroadcastEvent(
                kernel_id=batch_run.kernel_id,
                session_id=batch_run.session_id,
                reason=KernelLifecycleEventReason.SELF_TERMINATED,
            ),
        )
