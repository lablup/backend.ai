from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.idle_checker.types import (
    ExpiredIdleCheckBatchData,
    ExpiredIdleCheckData,
)
from ai.backend.manager.sokovan.idle_check.handlers.sweep import IdleCheckSweepHandler
from ai.backend.manager.sokovan.idle_check.sweep.types import (
    IdleCheckSweepReason,
    IdleCheckSweepReconcileInfo,
    IdleCheckSweepReport,
)

_NOW = datetime(2026, 7, 20, tzinfo=UTC)


def _expired_check(
    session_id: SessionId,
    checker_id: IdleCheckerID,
    *,
    seconds_ago: int,
    status: str,
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
    def grouped_due_rows_case(
        self,
    ) -> tuple[IdleCheckSweepReconcileInfo, list[IdleCheckSweepReport]]:
        first_session_id = SessionId(uuid4())
        second_session_id = SessionId(uuid4())
        first_checker_id = IdleCheckerID(uuid4())
        second_checker_id = IdleCheckerID(uuid4())
        first_check = _expired_check(
            first_session_id,
            second_checker_id,
            seconds_ago=10,
            status="expired",
            message="network timeout",
        )
        second_check = _expired_check(
            first_session_id,
            first_checker_id,
            seconds_ago=20,
            status="expired",
            message="maximum lifetime exceeded",
        )
        third_check = _expired_check(
            second_session_id,
            first_checker_id,
            seconds_ago=5,
            status="expired",
            message="maximum lifetime exceeded",
        )
        expected_reports = [
            IdleCheckSweepReport(
                session_id=first_session_id,
                reasons=[
                    IdleCheckSweepReason(
                        checker_id=second_checker_id,
                        expire_at=first_check.expire_at,
                        last_message=first_check.last_message,
                    ),
                    IdleCheckSweepReason(
                        checker_id=first_checker_id,
                        expire_at=second_check.expire_at,
                        last_message=second_check.last_message,
                    ),
                ],
            ),
            IdleCheckSweepReport(
                session_id=second_session_id,
                reasons=[
                    IdleCheckSweepReason(
                        checker_id=first_checker_id,
                        expire_at=third_check.expire_at,
                        last_message=third_check.last_message,
                    ),
                ],
            ),
        ]
        reconcile_info = IdleCheckSweepReconcileInfo(
            batch=ExpiredIdleCheckBatchData(
                checks=(first_check, second_check, third_check),
                now=_NOW,
            )
        )
        return reconcile_info, expected_reports

    async def test_groups_due_rows_by_session_and_keeps_each_reason(
        self,
        grouped_due_rows_case: tuple[IdleCheckSweepReconcileInfo, list[IdleCheckSweepReport]],
    ) -> None:
        reconcile_info, expected_reports = grouped_due_rows_case

        result = await IdleCheckSweepHandler().execute(reconcile_info)

        assert result.reports == expected_reports
        assert result.processed_count() == 2
        assert result.decisions() == ()

    async def test_empty_batch_returns_empty_result(self) -> None:
        reconcile_info = IdleCheckSweepReconcileInfo(
            batch=ExpiredIdleCheckBatchData(checks=(), now=_NOW)
        )

        result = await IdleCheckSweepHandler().execute(reconcile_info)

        assert result.reports == []
        assert result.processed_count() == 0
