from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.idle_checker.types import (
    ExpiredIdleCheckBatchData,
    ExpiredIdleCheckData,
)
from ai.backend.manager.sokovan.idle_check.handlers.sweep import IdleCheckSweepHandler
from ai.backend.manager.sokovan.idle_check.sweep.types import IdleCheckSweepReconcileInfo
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

_NOW = datetime(2026, 7, 20, tzinfo=UTC)


def _expired_check(
    session_id: SessionId,
    checker_id: IdleCheckerID,
    *,
    seconds_ago: int,
    status: IdleCheckPhase,
    message: str,
) -> ExpiredIdleCheckData:
    return ExpiredIdleCheckData(
        session_id=session_id,
        checker_id=checker_id,
        expire_at=_NOW - timedelta(seconds=seconds_ago),
        last_status=status,
        last_message=message,
    )


class TestIdleCheckSweepHandler:
    @pytest.fixture
    def scheduling_controller(self) -> AsyncMock:
        return AsyncMock(spec=SchedulingController)

    @pytest.fixture
    def grouped_due_rows_case(
        self,
    ) -> tuple[IdleCheckSweepReconcileInfo, list[SessionId]]:
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        first_checker_id = IdleCheckerID(UUID(int=1))
        second_checker_id = IdleCheckerID(UUID(int=2))
        first_check = _expired_check(
            first_session_id,
            second_checker_id,
            seconds_ago=10,
            status=IdleCheckPhase.IDLE_EXPIRED,
            message="network timeout",
        )
        second_check = _expired_check(
            first_session_id,
            first_checker_id,
            seconds_ago=20,
            status=IdleCheckPhase.IDLE_EXPIRED,
            message="maximum lifetime exceeded",
        )
        third_check = _expired_check(
            second_session_id,
            first_checker_id,
            seconds_ago=5,
            status=IdleCheckPhase.IDLE_EXPIRED,
            message="maximum lifetime exceeded",
        )
        reconcile_info = IdleCheckSweepReconcileInfo(
            batch=ExpiredIdleCheckBatchData(
                checks=(first_check, second_check, third_check),
                now=_NOW,
            )
        )
        return reconcile_info, [first_session_id, second_session_id]

    async def test_deduplicates_due_session_ids(
        self,
        scheduling_controller: AsyncMock,
        grouped_due_rows_case: tuple[IdleCheckSweepReconcileInfo, list[SessionId]],
    ) -> None:
        reconcile_info, expected_session_ids = grouped_due_rows_case
        handler = IdleCheckSweepHandler(cast(SchedulingController, scheduling_controller))

        result = await handler.execute(reconcile_info)

        assert result.session_ids == expected_session_ids
        assert result.processed_count() == 2
        assert result.decisions() == ()
        scheduling_controller.mark_sessions_for_termination.assert_awaited_once_with(
            expected_session_ids,
            reason=KernelLifecycleEventReason.IDLE_TIMEOUT.value,
            message="idle check timeout",
        )

    async def test_empty_batch_returns_empty_result(
        self,
        scheduling_controller: AsyncMock,
    ) -> None:
        reconcile_info = IdleCheckSweepReconcileInfo(
            batch=ExpiredIdleCheckBatchData(checks=(), now=_NOW)
        )
        handler = IdleCheckSweepHandler(cast(SchedulingController, scheduling_controller))

        result = await handler.execute(reconcile_info)

        assert result.session_ids == []
        assert result.processed_count() == 0
        scheduling_controller.mark_sessions_for_termination.assert_not_awaited()
