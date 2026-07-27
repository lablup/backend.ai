from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
    SessionLifetimeSpec,
    UtilizationKernelPolicy,
    UtilizationSpec,
    UtilizationThresholdEntry,
    UtilizationThresholdOperator,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationBatchAction,
    SessionUtilizationBatchActionResult,
    SessionUtilizationObservation,
)
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleCheckerContext,
)
from ai.backend.manager.sokovan.idle_check.checkers.utilization.checker import UtilizationChecker

_NOW = datetime(2026, 7, 25, 12, tzinfo=UTC)
_EXISTING_EXPIRE_AT = _NOW + timedelta(minutes=5)


class AssignmentFactory(Protocol):
    def __call__(
        self,
        *,
        thresholds: Sequence[UtilizationThresholdEntry],
        sessions: Sequence[IdleCheckSession],
        operator: UtilizationThresholdOperator = UtilizationThresholdOperator.AND,
        duration_seconds: int = 1800,
    ) -> CheckerAssignment: ...


def _threshold(
    metric_name: str,
    threshold: str,
    policy: UtilizationKernelPolicy = UtilizationKernelPolicy.AVERAGE,
) -> UtilizationThresholdEntry:
    return UtilizationThresholdEntry(
        metric_name=metric_name,
        threshold=Decimal(threshold),
        kernel_policy=policy,
    )


def _observation(
    entry: UtilizationThresholdEntry,
    value: str,
) -> SessionUtilizationObservation:
    return SessionUtilizationObservation(entry=entry, value=Decimal(value))


class TestUtilizationSpec:
    def test_rejects_non_positive_duration(self) -> None:
        with pytest.raises(ValidationError):
            UtilizationSpec(
                max_underutilized_duration_seconds=0,
                thresholds=[_threshold("cpu_util", "10")],
            )

    def test_rejects_duplicate_metrics(self) -> None:
        with pytest.raises(ValidationError):
            UtilizationSpec(
                max_underutilized_duration_seconds=1800,
                thresholds=[
                    _threshold("cpu_util", "10"),
                    _threshold("cpu_util", "20"),
                ],
            )

    def test_rejects_threshold_outside_percentage_range(self) -> None:
        with pytest.raises(ValidationError):
            _threshold("cpu_util", "100.1")


class TestUtilizationChecker:
    @pytest.fixture
    def metric_service(self) -> MagicMock:
        service = MagicMock(spec=MetricService)
        service.query_session_utilization_batch = AsyncMock()
        return service

    @pytest.fixture
    def checker(self, metric_service: MagicMock) -> UtilizationChecker:
        return UtilizationChecker(metric_service)

    @pytest.fixture
    def session(self) -> IdleCheckSession:
        return IdleCheckSession(
            session_id=SessionId(uuid4()),
            created_at=_NOW - timedelta(hours=1),
            starts_at=_NOW - timedelta(hours=1),
            expire_at=_EXISTING_EXPIRE_AT,
        )

    @pytest.fixture
    def assignment_factory(self) -> AssignmentFactory:
        def create_assignment(
            *,
            thresholds: Sequence[UtilizationThresholdEntry],
            sessions: Sequence[IdleCheckSession],
            operator: UtilizationThresholdOperator = UtilizationThresholdOperator.AND,
            duration_seconds: int = 1800,
        ) -> CheckerAssignment:
            return CheckerAssignment(
                definition=IdleCheckerDefinitionData(
                    checker_id=IdleCheckerID(uuid4()),
                    checker_type=CheckerType.UTILIZATION,
                    target_session_types=frozenset({SessionTypes.INTERACTIVE}),
                    spec=IdleCheckerSpec(
                        type=CheckerType.UTILIZATION,
                        utilization=UtilizationSpec(
                            max_underutilized_duration_seconds=duration_seconds,
                            thresholds_check_operator=operator,
                            thresholds=list(thresholds),
                        ),
                    ),
                ),
                sessions=sessions,
            )

        return create_assignment

    async def test_below_threshold_returns_idle(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> None:
        entry = _threshold("cpu_util", "10")
        metric_service.query_session_utilization_batch.return_value = (
            SessionUtilizationBatchActionResult(
                observations_by_check=[
                    {session.session_id: [_observation(entry, "9.9")]},
                ]
            )
        )

        judgments = await checker.judge(
            [assignment_factory(thresholds=[entry], sessions=[session])],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(judgments) == 1
        assert judgments[0].status is IdleCheckPhase.IDLE
        assert judgments[0].expire_at == _EXISTING_EXPIRE_AT

    @pytest.mark.parametrize(
        "expire_at",
        [
            _NOW,
            _NOW - timedelta(microseconds=1),
        ],
    )
    async def test_below_threshold_returns_idle_expired_when_deadline_has_elapsed(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        assignment_factory: AssignmentFactory,
        expire_at: datetime,
    ) -> None:
        session = IdleCheckSession(
            session_id=SessionId(uuid4()),
            created_at=_NOW - timedelta(hours=1),
            starts_at=_NOW - timedelta(hours=1),
            expire_at=expire_at,
        )
        entry = _threshold("cpu_util", "10")
        metric_service.query_session_utilization_batch.return_value = (
            SessionUtilizationBatchActionResult(
                observations_by_check=[
                    {session.session_id: [_observation(entry, "9.9")]},
                ]
            )
        )

        judgments = await checker.judge(
            [assignment_factory(thresholds=[entry], sessions=[session])],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(judgments) == 1
        assert judgments[0].status is IdleCheckPhase.IDLE_EXPIRED
        assert judgments[0].expire_at == expire_at

    @pytest.mark.parametrize("value", ["10", "10.1"])
    async def test_threshold_or_above_returns_active_and_refreshes_deadline(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
        value: str,
    ) -> None:
        entry = _threshold("cpu_util", "10")
        metric_service.query_session_utilization_batch.return_value = (
            SessionUtilizationBatchActionResult(
                observations_by_check=[
                    {session.session_id: [_observation(entry, value)]},
                ]
            )
        )

        judgments = await checker.judge(
            [
                assignment_factory(
                    thresholds=[entry],
                    sessions=[session],
                    duration_seconds=1800,
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(judgments) == 1
        assert judgments[0].status is IdleCheckPhase.ACTIVE
        assert judgments[0].expire_at == _NOW + timedelta(seconds=1800)

    @pytest.mark.parametrize(
        ("operator", "expected_status"),
        [
            (UtilizationThresholdOperator.AND, IdleCheckPhase.ACTIVE),
            (UtilizationThresholdOperator.OR, IdleCheckPhase.IDLE),
        ],
    )
    async def test_combines_metric_results_with_configured_operator(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
        operator: UtilizationThresholdOperator,
        expected_status: IdleCheckPhase,
    ) -> None:
        cpu_entry = _threshold("cpu_util", "10")
        mem_entry = _threshold("mem", "10")
        metric_service.query_session_utilization_batch.return_value = (
            SessionUtilizationBatchActionResult(
                observations_by_check=[
                    {
                        session.session_id: [
                            _observation(cpu_entry, "5"),
                            _observation(mem_entry, "50"),
                        ]
                    },
                ]
            )
        )

        judgments = await checker.judge(
            [
                assignment_factory(
                    thresholds=[cpu_entry, mem_entry],
                    sessions=[session],
                    operator=operator,
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert judgments[0].status is expected_status

    async def test_missing_observations_are_unknown(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> None:
        entry = _threshold("cpu_util", "10")
        metric_service.query_session_utilization_batch.return_value = (
            SessionUtilizationBatchActionResult(observations_by_check=[{}])
        )

        judgments = await checker.judge(
            [assignment_factory(thresholds=[entry], sessions=[session])],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert judgments == []

    async def test_batches_assignments_in_one_service_call(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> None:
        second_session = IdleCheckSession(
            session_id=SessionId(uuid4()),
            created_at=session.created_at,
            starts_at=session.starts_at,
            expire_at=_EXISTING_EXPIRE_AT,
        )
        first_entry = _threshold("cpu_util", "10")
        second_entry = _threshold("cpu_util", "20")
        metric_service.query_session_utilization_batch.return_value = (
            SessionUtilizationBatchActionResult(
                observations_by_check=[
                    {session.session_id: [_observation(first_entry, "5")]},
                    {second_session.session_id: [_observation(second_entry, "15")]},
                ]
            )
        )

        judgments = await checker.judge(
            [
                assignment_factory(thresholds=[first_entry], sessions=[session]),
                assignment_factory(thresholds=[second_entry], sessions=[second_session]),
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert [judgment.status for judgment in judgments] == [
            IdleCheckPhase.IDLE,
            IdleCheckPhase.IDLE,
        ]
        metric_service.query_session_utilization_batch.assert_awaited_once()
        action = metric_service.query_session_utilization_batch.await_args.args[0]
        assert isinstance(action, SessionUtilizationBatchAction)
        assert action.evaluation_time == _NOW
        assert [check.session_ids for check in action.checks] == [
            [session.session_id],
            [second_session.session_id],
        ]

    async def test_mismatched_spec_is_ignored(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        session: IdleCheckSession,
    ) -> None:
        assignment = CheckerAssignment(
            definition=IdleCheckerDefinitionData(
                checker_id=IdleCheckerID(uuid4()),
                checker_type=CheckerType.SESSION_LIFETIME,
                target_session_types=frozenset({SessionTypes.INTERACTIVE}),
                spec=IdleCheckerSpec(
                    type=CheckerType.SESSION_LIFETIME,
                    session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
                ),
            ),
            sessions=[session],
        )

        judgments = await checker.judge(
            [assignment],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert judgments == []
        metric_service.query_session_utilization_batch.assert_not_awaited()
