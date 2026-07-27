from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
    SessionLifetimeSpec,
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationAction,
    SessionUtilizationActionResult,
    SessionUtilizationObservation,
    SessionUtilizationQuery,
)
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleCheckerContext,
)
from ai.backend.manager.sokovan.idle_check.checkers.utilization import UtilizationChecker

_NOW = datetime(2026, 7, 25, 12, tzinfo=UTC)
_DURATION_SECONDS = 1800
_EXISTING_EXPIRE_AT = _NOW + timedelta(minutes=5)


class AssignmentFactory(Protocol):
    def __call__(
        self,
        *,
        preset_id: UUID,
        threshold: Decimal,
        sessions: Sequence[IdleCheckSession],
        duration_seconds: int = _DURATION_SECONDS,
    ) -> CheckerAssignment: ...


def _session(
    *,
    expire_at: datetime = _EXISTING_EXPIRE_AT,
) -> IdleCheckSession:
    return IdleCheckSession(
        session_id=SessionId(uuid4()),
        created_at=_NOW - timedelta(hours=1),
        starts_at=_NOW - timedelta(hours=1),
        expire_at=expire_at,
    )


class TestUtilizationSpec:
    def test_rejects_non_positive_duration(self) -> None:
        with pytest.raises(ValidationError):
            UtilizationSpec(
                max_underutilized_duration_seconds=0,
                threshold=UtilizationThresholdEntry(
                    preset_id=uuid4(),
                    threshold=Decimal("10"),
                ),
            )

    @pytest.mark.parametrize("threshold", [Decimal("-0.1"), Decimal("100.1")])
    def test_rejects_threshold_outside_percentage_range(self, threshold: Decimal) -> None:
        with pytest.raises(ValidationError):
            UtilizationThresholdEntry(
                preset_id=uuid4(),
                threshold=threshold,
            )


class TestUtilizationChecker:
    @pytest.fixture()
    def metric_service(self) -> MagicMock:
        service = MagicMock(spec=MetricService)
        service.query_session_utilization = AsyncMock()
        return service

    @pytest.fixture()
    def checker(self, metric_service: MagicMock) -> UtilizationChecker:
        return UtilizationChecker(metric_service)

    @pytest.fixture()
    def assignment_factory(self) -> AssignmentFactory:
        def create_assignment(
            *,
            preset_id: UUID,
            threshold: Decimal,
            sessions: Sequence[IdleCheckSession],
            duration_seconds: int = _DURATION_SECONDS,
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
                            threshold=UtilizationThresholdEntry(
                                preset_id=preset_id,
                                threshold=threshold,
                            ),
                        ),
                    ),
                ),
                sessions=sessions,
            )

        return create_assignment

    async def test_batches_all_assignments_into_one_metric_service_call(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        first_preset_id = uuid4()
        second_preset_id = uuid4()
        first_session = _session()
        second_session = _session()
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_preset={
                first_preset_id: {
                    first_session.session_id: SessionUtilizationObservation(
                        preset_id=first_preset_id,
                        value=Decimal("5"),
                    )
                },
                second_preset_id: {
                    second_session.session_id: SessionUtilizationObservation(
                        preset_id=second_preset_id,
                        value=Decimal("15"),
                    )
                },
            }
        )

        judgments = await checker.judge(
            [
                assignment_factory(
                    preset_id=first_preset_id,
                    threshold=Decimal("10"),
                    sessions=[first_session],
                ),
                assignment_factory(
                    preset_id=second_preset_id,
                    threshold=Decimal("20"),
                    sessions=[second_session],
                ),
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert [judgment.status for judgment in judgments] == [
            IdleCheckPhase.IDLE,
            IdleCheckPhase.IDLE,
        ]
        metric_service.query_session_utilization.assert_awaited_once_with(
            SessionUtilizationAction(
                queries=[
                    SessionUtilizationQuery(
                        preset_id=first_preset_id,
                        session_ids=[first_session.session_id],
                    ),
                    SessionUtilizationQuery(
                        preset_id=second_preset_id,
                        session_ids=[second_session.session_id],
                    ),
                ],
                evaluation_time=_NOW,
            )
        )

    async def test_underutilized_result_uses_existing_deadline(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        preset_id = uuid4()
        session = _session()
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_preset={
                preset_id: {
                    session.session_id: SessionUtilizationObservation(
                        preset_id=preset_id,
                        value=Decimal("9.9"),
                    )
                }
            }
        )

        judgments = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[session],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(judgments) == 1
        assert judgments[0].status is IdleCheckPhase.IDLE
        assert judgments[0].expire_at == _EXISTING_EXPIRE_AT
        assert f"metric=[preset_id={preset_id}, value=9.9/10]" in judgments[0].message

    @pytest.mark.parametrize(
        ("expire_at", "expected_status"),
        [
            (_NOW + timedelta(seconds=1), IdleCheckPhase.IDLE),
            (_NOW, IdleCheckPhase.IDLE_EXPIRED),
        ],
    )
    async def test_existing_idle_result_preserves_deadline(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        assignment_factory: AssignmentFactory,
        expire_at: datetime,
        expected_status: IdleCheckPhase,
    ) -> None:
        preset_id = uuid4()
        session = _session(expire_at=expire_at)
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_preset={
                preset_id: {
                    session.session_id: SessionUtilizationObservation(
                        preset_id=preset_id,
                        value=Decimal("5"),
                    )
                }
            }
        )

        judgments = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[session],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(judgments) == 1
        assert judgments[0].status is expected_status
        assert judgments[0].expire_at == expire_at

    @pytest.mark.parametrize("value", [Decimal("10"), Decimal("10.1")])
    async def test_threshold_or_above_returns_active_and_refreshes_deadline(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        assignment_factory: AssignmentFactory,
        value: Decimal,
    ) -> None:
        preset_id = uuid4()
        session = _session()
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_preset={
                preset_id: {
                    session.session_id: SessionUtilizationObservation(
                        preset_id=preset_id,
                        value=value,
                    )
                }
            }
        )

        judgments = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[session],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(judgments) == 1
        assert judgments[0].status is IdleCheckPhase.ACTIVE
        assert judgments[0].expire_at == _NOW + timedelta(seconds=_DURATION_SECONDS)

    async def test_missing_observation_is_ignored(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        preset_id = uuid4()
        metric_service.query_session_utilization.return_value = SessionUtilizationActionResult(
            observations_by_preset={}
        )

        judgments = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[_session()],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert judgments == []

    async def test_mismatched_spec_is_ignored(
        self,
        checker: UtilizationChecker,
        metric_service: MagicMock,
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
            sessions=[_session()],
        )

        judgments = await checker.judge(
            [assignment],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert judgments == []
        metric_service.query_session_utilization.assert_not_awaited()
