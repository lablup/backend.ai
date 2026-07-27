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
    UtilizationSpec,
    UtilizationThresholdEntry,
    UtilizationThresholdOperator,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import KernelAggregationMode, SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.data.metric.types import SessionUtilizationMetricThreshold
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationAction,
    SessionUtilizationActionResult,
    SessionUtilizationObservation,
)
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleCheckerContext,
)
from ai.backend.manager.sokovan.idle_check.checkers.utilization import UtilizationChecker

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


class TestUtilizationSpec:
    def test_rejects_non_positive_duration(self) -> None:
        with pytest.raises(ValidationError):
            UtilizationSpec(
                max_underutilized_duration_seconds=0,
                thresholds=[
                    UtilizationThresholdEntry(
                        metric_name="cpu_util",
                        threshold=Decimal("10"),
                        kernel_aggregation=KernelAggregationMode.AVERAGE,
                    )
                ],
            )

    def test_rejects_duplicate_metrics(self) -> None:
        with pytest.raises(ValidationError):
            UtilizationSpec(
                max_underutilized_duration_seconds=1800,
                thresholds=[
                    UtilizationThresholdEntry(
                        metric_name="cpu_util",
                        threshold=Decimal("10"),
                        kernel_aggregation=KernelAggregationMode.AVERAGE,
                    ),
                    UtilizationThresholdEntry(
                        metric_name="cpu_util",
                        threshold=Decimal("20"),
                        kernel_aggregation=KernelAggregationMode.AVERAGE,
                    ),
                ],
            )

    def test_rejects_threshold_outside_percentage_range(self) -> None:
        with pytest.raises(ValidationError):
            UtilizationThresholdEntry(
                metric_name="cpu_util",
                threshold=Decimal("100.1"),
                kernel_aggregation=KernelAggregationMode.AVERAGE,
            )


class TestUtilizationChecker:
    @pytest.fixture
    def metric_service(self) -> MagicMock:
        service = MagicMock(spec=MetricService)
        service.query_session_utilization = AsyncMock()
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
        entry = UtilizationThresholdEntry(
            metric_name="cpu_util",
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_session={
                session.session_id: [
                    SessionUtilizationObservation(
                        entry=SessionUtilizationMetricThreshold(
                            metric_name="cpu_util",
                            time_window_seconds=None,
                            threshold=Decimal("10"),
                            kernel_aggregation=KernelAggregationMode.AVERAGE,
                        ),
                        value=Decimal("9.9"),
                    )
                ],
            }
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
        entry = UtilizationThresholdEntry(
            metric_name="cpu_util",
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_session={
                session.session_id: [
                    SessionUtilizationObservation(
                        entry=SessionUtilizationMetricThreshold(
                            metric_name="cpu_util",
                            time_window_seconds=None,
                            threshold=Decimal("10"),
                            kernel_aggregation=KernelAggregationMode.AVERAGE,
                        ),
                        value=Decimal("9.9"),
                    )
                ],
            }
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
        entry = UtilizationThresholdEntry(
            metric_name="cpu_util",
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_session={
                session.session_id: [
                    SessionUtilizationObservation(
                        entry=SessionUtilizationMetricThreshold(
                            metric_name="cpu_util",
                            time_window_seconds=None,
                            threshold=Decimal("10"),
                            kernel_aggregation=KernelAggregationMode.AVERAGE,
                        ),
                        value=Decimal(value),
                    )
                ],
            }
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
        cpu_entry = UtilizationThresholdEntry(
            metric_name="cpu_util",
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        mem_entry = UtilizationThresholdEntry(
            metric_name="mem",
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_session={
                session.session_id: [
                    SessionUtilizationObservation(
                        entry=SessionUtilizationMetricThreshold(
                            metric_name="cpu_util",
                            time_window_seconds=None,
                            threshold=Decimal("10"),
                            kernel_aggregation=KernelAggregationMode.AVERAGE,
                        ),
                        value=Decimal("5"),
                    ),
                    SessionUtilizationObservation(
                        entry=SessionUtilizationMetricThreshold(
                            metric_name="mem",
                            time_window_seconds=None,
                            threshold=Decimal("10"),
                            kernel_aggregation=KernelAggregationMode.AVERAGE,
                        ),
                        value=Decimal("50"),
                    ),
                ]
            }
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
        entry = UtilizationThresholdEntry(
            metric_name="cpu_util",
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_session={}
        )

        judgments = await checker.judge(
            [assignment_factory(thresholds=[entry], sessions=[session])],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert judgments == []

    async def test_queries_each_assignment_separately(
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
        first_entry = UtilizationThresholdEntry(
            metric_name="cpu_util",
            threshold=Decimal("10"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        second_entry = UtilizationThresholdEntry(
            metric_name="cpu_util",
            threshold=Decimal("20"),
            kernel_aggregation=KernelAggregationMode.AVERAGE,
        )
        metric_service.query_session_utilization.side_effect = [
            SessionUtilizationActionResult(
                observations_by_session={
                    session.session_id: [
                        SessionUtilizationObservation(
                            entry=SessionUtilizationMetricThreshold(
                                metric_name="cpu_util",
                                time_window_seconds=None,
                                threshold=Decimal("10"),
                                kernel_aggregation=KernelAggregationMode.AVERAGE,
                            ),
                            value=Decimal("5"),
                        )
                    ],
                }
            ),
            SessionUtilizationActionResult(
                observations_by_session={
                    second_session.session_id: [
                        SessionUtilizationObservation(
                            entry=SessionUtilizationMetricThreshold(
                                metric_name="cpu_util",
                                time_window_seconds=None,
                                threshold=Decimal("20"),
                                kernel_aggregation=KernelAggregationMode.AVERAGE,
                            ),
                            value=Decimal("15"),
                        )
                    ],
                }
            ),
        ]

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
        assert metric_service.query_session_utilization.await_count == 2
        actions = [
            call.args[0] for call in metric_service.query_session_utilization.await_args_list
        ]
        assert all(isinstance(action, SessionUtilizationAction) for action in actions)
        assert [action.evaluation_time for action in actions] == [_NOW, _NOW]
        assert [action.thresholds for action in actions] == [
            [
                SessionUtilizationMetricThreshold(
                    metric_name="cpu_util",
                    time_window_seconds=None,
                    threshold=Decimal("10"),
                    kernel_aggregation=KernelAggregationMode.AVERAGE,
                )
            ],
            [
                SessionUtilizationMetricThreshold(
                    metric_name="cpu_util",
                    time_window_seconds=None,
                    threshold=Decimal("20"),
                    kernel_aggregation=KernelAggregationMode.AVERAGE,
                )
            ],
        ]
        assert [action.session_ids for action in actions] == [
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
        metric_service.query_session_utilization.assert_not_awaited()
