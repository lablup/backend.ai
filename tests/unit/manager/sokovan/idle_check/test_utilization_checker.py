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
    MetricLabel,
    SessionLifetimeSpec,
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession, SessionUtilizationQuery
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData
from ai.backend.manager.repositories.metric.repository import MetricRepository
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
        preset_id: PrometheusQueryPresetID,
        threshold: Decimal,
        sessions: Sequence[IdleCheckSession],
        duration_seconds: int = _DURATION_SECONDS,
        filter_labels: dict[str, str] | None = None,
    ) -> CheckerAssignment: ...


def _query(
    preset_id: PrometheusQueryPresetID,
    filter_labels: dict[str, str] | None = None,
) -> SessionUtilizationQuery:
    return SessionUtilizationQuery(
        preset_id=preset_id,
        filter_labels=tuple(sorted((filter_labels or {}).items())),
        group_labels=("session_id",),
    )


def _session(
    *,
    expire_at: datetime | None = _EXISTING_EXPIRE_AT,
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
                    preset_id=PrometheusQueryPresetID(uuid4()),
                    threshold=Decimal("10"),
                ),
            )

    def test_rejects_duplicate_filter_label_keys(self) -> None:
        with pytest.raises(ValidationError):
            UtilizationThresholdEntry(
                preset_id=PrometheusQueryPresetID(uuid4()),
                threshold=Decimal("10"),
                filter_labels=[
                    MetricLabel(key="container_metric_name", value="cpu_util"),
                    MetricLabel(key="container_metric_name", value="mem"),
                ],
            )

    def test_query_key_canonicalizes_label_order(self) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())

        def entry(filter_order: list[tuple[str, str]], group: list[str]) -> SessionUtilizationQuery:
            return SessionUtilizationQuery.from_threshold(
                UtilizationThresholdEntry(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    filter_labels=[MetricLabel(key=k, value=v) for k, v in filter_order],
                    group_labels=group,
                )
            )

        assert entry([("a", "1"), ("b", "2")], ["session_id", "device"]) == entry(
            [("b", "2"), ("a", "1")], ["device", "session_id", "device"]
        )


class TestUtilizationChecker:
    @pytest.fixture()
    def metric_repository(self) -> MagicMock:
        repository = MagicMock(spec=MetricRepository)
        repository.query_session_utilization_metrics = AsyncMock()
        return repository

    @pytest.fixture()
    def checker(self, metric_repository: MagicMock) -> UtilizationChecker:
        return UtilizationChecker(metric_repository)

    @pytest.fixture()
    def assignment_factory(self) -> AssignmentFactory:
        def create_assignment(
            *,
            preset_id: PrometheusQueryPresetID,
            threshold: Decimal,
            sessions: Sequence[IdleCheckSession],
            duration_seconds: int = _DURATION_SECONDS,
            filter_labels: dict[str, str] | None = None,
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
                                filter_labels=[
                                    MetricLabel(key=key, value=value)
                                    for key, value in (filter_labels or {}).items()
                                ],
                            ),
                        ),
                    ),
                ),
                sessions=sessions,
            )

        return create_assignment

    async def test_batches_all_assignments_into_one_repository_call(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        first_preset_id = PrometheusQueryPresetID(uuid4())
        second_preset_id = PrometheusQueryPresetID(uuid4())
        first_session = _session()
        second_session = _session()
        metric_repository.query_session_utilization_metrics.return_value = {
            _query(first_preset_id): {first_session.session_id: Decimal("5")},
            _query(second_preset_id): {second_session.session_id: Decimal("15")},
        }

        decisions = await checker.judge(
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

        assert all(not decision.is_active for decision in decisions)
        metric_repository.query_session_utilization_metrics.assert_awaited_once_with(
            {
                _query(first_preset_id): [first_session.session_id],
                _query(second_preset_id): [second_session.session_id],
            },
            evaluation_time=_NOW,
        )

    async def test_merges_sessions_sharing_a_preset_into_one_query(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())
        first_session = _session()
        second_session = _session()
        metric_repository.query_session_utilization_metrics.return_value = {
            _query(preset_id): {
                first_session.session_id: Decimal("5"),
                second_session.session_id: Decimal("15"),
            },
        }

        decisions = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[first_session],
                ),
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[second_session],
                ),
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert [decision.is_active for decision in decisions] == [False, True]
        metric_repository.query_session_utilization_metrics.assert_awaited_once_with(
            {
                _query(preset_id): [first_session.session_id, second_session.session_id],
            },
            evaluation_time=_NOW,
        )

    async def test_same_preset_with_different_labels_batches_separately(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())
        cpu_labels = {"container_metric_name": "cpu_util"}
        mem_labels = {"container_metric_name": "mem"}
        first_session = _session()
        second_session = _session()
        metric_repository.query_session_utilization_metrics.return_value = {
            _query(preset_id, cpu_labels): {first_session.session_id: Decimal("5")},
            _query(preset_id, mem_labels): {second_session.session_id: Decimal("15")},
        }

        decisions = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[first_session],
                    filter_labels=cpu_labels,
                ),
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[second_session],
                    filter_labels=mem_labels,
                ),
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert [decision.is_active for decision in decisions] == [False, True]
        metric_repository.query_session_utilization_metrics.assert_awaited_once_with(
            {
                _query(preset_id, cpu_labels): [first_session.session_id],
                _query(preset_id, mem_labels): [second_session.session_id],
            },
            evaluation_time=_NOW,
        )

    async def test_underutilized_result_uses_existing_deadline(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())
        session = _session()
        metric_repository.query_session_utilization_metrics.return_value = {
            _query(preset_id): {session.session_id: Decimal("9.9")},
        }

        decisions = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[session],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(decisions) == 1
        assert not decisions[0].is_active
        assert decisions[0].expire_at == _EXISTING_EXPIRE_AT
        assert f"metric=[preset_id={preset_id}, value=9.9/10]" in decisions[0].message

    async def test_first_underutilized_result_initializes_deadline(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())
        session = _session(expire_at=None)
        metric_repository.query_session_utilization_metrics.return_value = {
            _query(preset_id): {session.session_id: Decimal("9.9")},
        }

        decisions = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[session],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(decisions) == 1
        assert not decisions[0].is_active
        assert decisions[0].expire_at == _NOW + timedelta(seconds=_DURATION_SECONDS)

    @pytest.mark.parametrize("expire_at", [_NOW + timedelta(seconds=1), _NOW])
    async def test_existing_idle_result_preserves_deadline(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
        expire_at: datetime,
    ) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())
        session = _session(expire_at=expire_at)
        metric_repository.query_session_utilization_metrics.return_value = {
            _query(preset_id): {session.session_id: Decimal("5")},
        }

        decisions = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[session],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(decisions) == 1
        assert not decisions[0].is_active
        assert decisions[0].expire_at == expire_at

    @pytest.mark.parametrize("value", [Decimal("10"), Decimal("10.1")])
    async def test_threshold_or_above_returns_active_and_refreshes_deadline(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
        value: Decimal,
    ) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())
        session = _session()
        metric_repository.query_session_utilization_metrics.return_value = {
            _query(preset_id): {session.session_id: value},
        }

        decisions = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[session],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert len(decisions) == 1
        assert decisions[0].is_active
        assert decisions[0].expire_at == _NOW + timedelta(seconds=_DURATION_SECONDS)

    async def test_missing_observation_is_ignored(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
        assignment_factory: AssignmentFactory,
    ) -> None:
        preset_id = PrometheusQueryPresetID(uuid4())
        metric_repository.query_session_utilization_metrics.return_value = {}

        decisions = await checker.judge(
            [
                assignment_factory(
                    preset_id=preset_id,
                    threshold=Decimal("10"),
                    sessions=[_session()],
                )
            ],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert decisions == []

    async def test_mismatched_spec_is_ignored(
        self,
        checker: UtilizationChecker,
        metric_repository: MagicMock,
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

        decisions = await checker.judge(
            [assignment],
            context=IdleCheckerContext(current_time=_NOW),
        )

        assert decisions == []
        metric_repository.query_session_utilization_metrics.assert_not_awaited()
