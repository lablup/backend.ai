"""The history DataLoader paths: each row is answered for through its session or
deployment."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.v2.ops.result import BulkFieldOpsResult
from ai.backend.manager.api.adapters.scheduling_history.adapter import SchedulingHistoryAdapter
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.session.types import SchedulingResult, SessionSchedulingHistoryData
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.repository import EntityNotFoundError

READABLE = SessionSchedulingHistoryID(uuid.uuid4())
DENIED = SessionSchedulingHistoryID(uuid.uuid4())
ABSENT = SessionSchedulingHistoryID(uuid.uuid4())


@pytest.fixture
def readable() -> SessionSchedulingHistoryData:
    return SessionSchedulingHistoryData(
        id=READABLE,
        session_id=SessionId(uuid.uuid4()),
        phase="schedule",
        from_status=None,
        to_status=None,
        result=SchedulingResult.SUCCESS,
        error_code=None,
        message="",
        sub_steps=[],
        attempts=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this session")


@pytest.fixture
def processors(readable: SessionSchedulingHistoryData, denial: GenericForbidden) -> MagicMock:
    processors = MagicMock()
    processors.scheduling_history.bulk_get_session_histories.run = AsyncMock(
        return_value=BulkFieldOpsResult(successes={READABLE: readable}, errors={DENIED: denial})
    )
    processors.scheduling_history.bulk_get_kernel_histories.run = AsyncMock(
        side_effect=EntityNotFoundError("No field row matches the given ids")
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> SchedulingHistoryAdapter:
    return SchedulingHistoryAdapter(processors.scheduling_history, processors.resource_slot)


async def test_session_histories_answer_per_id(
    adapter: SchedulingHistoryAdapter,
    processors: MagicMock,
    readable: SessionSchedulingHistoryData,
    denial: GenericForbidden,
) -> None:
    nodes = await adapter.batch_load_session_histories_by_ids([READABLE, DENIED, ABSENT])

    node, refused, missing = nodes
    assert node is not None and not isinstance(node, Exception)
    assert node.id == readable.id
    # A denial reaches the resolver; an id matching nothing stays None.
    assert refused is denial
    assert missing is None
    action = processors.scheduling_history.bulk_get_session_histories.run.await_args.args[0]
    assert list(action.field_ids()) == [READABLE, DENIED, ABSENT]


async def test_a_batch_naming_no_row_is_every_id_missing(
    adapter: SchedulingHistoryAdapter,
) -> None:
    ids = [KernelSchedulingHistoryID(uuid.uuid4()), KernelSchedulingHistoryID(uuid.uuid4())]
    assert await adapter.batch_load_kernel_histories_by_ids(ids) == [None, None]


async def test_no_ids_read_nothing(
    adapter: SchedulingHistoryAdapter, processors: MagicMock
) -> None:
    assert await adapter.batch_load_session_histories_by_ids([]) == []
    assert await adapter.batch_load_kernel_histories_by_ids([]) == []
    assert await adapter.batch_load_deployment_histories_by_ids([]) == []
    assert await adapter.batch_load_route_histories_by_ids([]) == []
    processors.scheduling_history.bulk_get_session_histories.run.assert_not_awaited()
    processors.scheduling_history.bulk_get_kernel_histories.run.assert_not_awaited()


def _kernel_history() -> KernelSchedulingHistoryData:
    return KernelSchedulingHistoryData(
        id=KernelSchedulingHistoryID(uuid.uuid4()),
        kernel_id=KernelId(uuid.uuid4()),
        session_id=SessionId(uuid.uuid4()),
        phase="schedule",
        from_status=None,
        to_status=None,
        result=SchedulingResult.SUCCESS,
        error_code=None,
        message="",
        attempts=1,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


async def test_kernel_histories_keep_the_given_order(processors: MagicMock) -> None:
    first, second = _kernel_history(), _kernel_history()
    processors.scheduling_history.bulk_get_kernel_histories.run = AsyncMock(
        return_value=BulkFieldOpsResult(successes={second.id: second, first.id: first}, errors={})
    )
    adapter = SchedulingHistoryAdapter(processors.scheduling_history, processors.resource_slot)

    nodes = await adapter.batch_load_kernel_histories_by_ids([first.id, second.id])

    assert [node.id for node in nodes if node is not None and not isinstance(node, Exception)] == [
        first.id,
        second.id,
    ]
