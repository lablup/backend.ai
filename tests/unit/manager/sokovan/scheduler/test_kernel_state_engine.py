from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.sokovan.scheduler.kernel.state_engine import KernelStateEngine


@pytest.fixture
def repository() -> AsyncMock:
    repository = AsyncMock()
    repository.update_kernel_status_cancelled.return_value = True
    return repository


@pytest.fixture
def event_producer() -> AsyncMock:
    return AsyncMock()


async def test_last_kernel_cancelled_anycasts_session_cancelled(
    repository: AsyncMock, event_producer: AsyncMock
) -> None:
    repository.check_and_cancel_session_if_needed.return_value = True
    session_id = SessionId(uuid.uuid4())

    await KernelStateEngine(repository, event_producer).mark_kernel_cancelled(
        KernelId(uuid.uuid4()), session_id, "image-pull-failed"
    )

    event = event_producer.anycast_event.await_args.args[0]
    assert (event.session_id, event.status, event.reason) == (
        session_id,
        "CANCELLED",
        "image-pull-failed",
    )
    event_producer.broadcast_events_batch.assert_not_awaited()


async def test_session_not_cancelled_is_not_anycast(
    repository: AsyncMock, event_producer: AsyncMock
) -> None:
    repository.check_and_cancel_session_if_needed.return_value = False

    await KernelStateEngine(repository, event_producer).mark_kernel_cancelled(
        KernelId(uuid.uuid4()), SessionId(uuid.uuid4()), "image-pull-failed"
    )

    event_producer.anycast_event.assert_not_awaited()
