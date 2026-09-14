from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    MetricLabel,
    SessionLifetimeSpec,
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.exception import PrometheusQueryPresetInvalidLabel
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.models.idle_checker.creators import IdleCheckerCreator
from ai.backend.manager.models.idle_checker.updaters import IdleCheckerUpdater
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import (
    SessionIdleCheckBatchResult,
    SessionIdleCheckPair,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.idle_checker.actions.create import CreateIdleCheckerAction
from ai.backend.manager.services.idle_checker.actions.exclude_sessions import (
    ExcludeSessionIdleChecksAction,
)
from ai.backend.manager.services.idle_checker.actions.include_sessions import (
    IncludeSessionIdleChecksAction,
)
from ai.backend.manager.services.idle_checker.actions.update import UpdateIdleCheckerAction
from ai.backend.manager.services.idle_checker.service import IdleCheckerService
from ai.backend.manager.types import OptionalState

_PRESET_ID = PrometheusQueryPresetID(uuid4())


def _utilization_spec(
    filter_labels: dict[str, str] | None = None,
    group_labels: list[str] | None = None,
) -> IdleCheckerSpec:
    return IdleCheckerSpec(
        type=CheckerType.UTILIZATION,
        utilization=UtilizationSpec(
            max_underutilized_duration_seconds=600,
            threshold=UtilizationThresholdEntry(
                preset_id=_PRESET_ID,
                threshold=Decimal("5"),
                filter_labels=[
                    MetricLabel(key=key, value=value)
                    for key, value in (filter_labels or {}).items()
                ],
                group_labels=group_labels or ["session_id"],
            ),
        ),
    )


def _create_action(spec: IdleCheckerSpec) -> CreateIdleCheckerAction:
    return CreateIdleCheckerAction(
        creator=IdleCheckerCreator(
            name="test-checker",
            description=None,
            target_session_types=[SessionTypes.INTERACTIVE],
            initial_grace_period_seconds=0,
            spec=spec,
        )
    )


class TestIdleCheckerSpecLabelValidation:
    @pytest.fixture()
    def preset(self) -> PrometheusQueryPresetData:
        now = datetime.now(tz=UTC)
        return PrometheusQueryPresetData(
            id=_PRESET_ID,
            name="container-utilization",
            description=None,
            rank=0,
            category_id=None,
            metric_name="backendai_container_utilization",
            query_template="sum by (${{group_by}})(backendai_container_utilization{${{labels}}})",
            time_window="5m",
            filter_labels=["container_metric_name", "session_id"],
            group_labels=["session_id", "device"],
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture()
    def ops_repository(self) -> MagicMock:
        ops_repository = MagicMock(spec=OpsRepository)
        ops_repository.create_global_entity = AsyncMock()
        ops_repository.update = AsyncMock()
        return ops_repository

    @pytest.fixture()
    def preset_repository(self, preset: PrometheusQueryPresetData) -> MagicMock:
        preset_repository = MagicMock(spec=PrometheusQueryPresetRepository)
        preset_repository.get_by_id = AsyncMock(return_value=preset)
        return preset_repository

    @pytest.fixture()
    def service(
        self,
        ops_repository: MagicMock,
        preset_repository: MagicMock,
    ) -> IdleCheckerService:
        return IdleCheckerService(
            MagicMock(spec=IdleCheckerRepository), preset_repository, ops_repository
        )

    async def test_create_with_allowed_labels_passes(
        self,
        service: IdleCheckerService,
        ops_repository: MagicMock,
    ) -> None:
        spec = _utilization_spec(
            filter_labels={"container_metric_name": "cpu_util"},
            group_labels=["session_id", "device"],
        )

        await service.create(_create_action(spec))

        ops_repository.create_global_entity.assert_awaited_once()

    @pytest.mark.parametrize(
        "spec",
        [
            _utilization_spec(filter_labels={"unknown_label": "x"}),
            _utilization_spec(group_labels=["project_id"]),
        ],
    )
    async def test_create_with_unsupported_labels_rejected(
        self,
        service: IdleCheckerService,
        ops_repository: MagicMock,
        spec: IdleCheckerSpec,
    ) -> None:
        with pytest.raises(PrometheusQueryPresetInvalidLabel):
            await service.create(_create_action(spec))
        ops_repository.create_global_entity.assert_not_awaited()

    async def test_non_utilization_spec_skips_preset_lookup(
        self,
        service: IdleCheckerService,
        preset_repository: MagicMock,
    ) -> None:
        spec = IdleCheckerSpec(
            type=CheckerType.SESSION_LIFETIME,
            session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
        )

        await service.create(_create_action(spec))

        preset_repository.get_by_id.assert_not_awaited()

    async def test_update_validates_replacement_spec(
        self,
        service: IdleCheckerService,
        ops_repository: MagicMock,
    ) -> None:
        action = UpdateIdleCheckerAction(
            updater=IdleCheckerUpdater(
                checker_id=IdleCheckerID(uuid4()),
                spec=OptionalState.update(_utilization_spec(filter_labels={"unknown_label": "x"})),
            )
        )

        with pytest.raises(PrometheusQueryPresetInvalidLabel):
            await service.update(action)
        ops_repository.update.assert_not_awaited()

    async def test_update_without_spec_skips_validation(
        self,
        service: IdleCheckerService,
        ops_repository: MagicMock,
        preset_repository: MagicMock,
    ) -> None:
        action = UpdateIdleCheckerAction(
            updater=IdleCheckerUpdater(
                checker_id=IdleCheckerID(uuid4()),
                name=OptionalState.update("renamed"),
            )
        )

        await service.update(action)

        preset_repository.get_by_id.assert_not_awaited()
        ops_repository.update.assert_awaited_once()


class TestSessionIdleCheckTargetHandoff:
    @pytest.fixture()
    def repository(self) -> MagicMock:
        repository = MagicMock(spec=IdleCheckerRepository)
        empty_result = SessionIdleCheckBatchResult(results=[])
        repository.batch_exclude_session_idle_checks = AsyncMock(return_value=empty_result)
        repository.batch_include_session_idle_checks = AsyncMock(return_value=empty_result)
        return repository

    @pytest.fixture()
    def service(self, repository: MagicMock) -> IdleCheckerService:
        return IdleCheckerService(
            repository,
            MagicMock(spec=PrometheusQueryPresetRepository),
            MagicMock(spec=OpsRepository),
        )

    async def test_exclude_hands_the_pairs_over_as_named(
        self,
        service: IdleCheckerService,
        repository: MagicMock,
    ) -> None:
        """The pairs reach the repository in the order named, a repeat included: the
        result answers per named pair, so the service drops nothing."""
        checker_id = IdleCheckerID(uuid4())
        user_id = UserID(uuid4())
        first_pair = SessionIdleCheckPair(session_id=SessionId(uuid4()), checker_id=checker_id)
        second_pair = SessionIdleCheckPair(session_id=SessionId(uuid4()), checker_id=checker_id)

        await service.exclude_sessions(
            ExcludeSessionIdleChecksAction(
                targets=[first_pair, second_pair, first_pair],
                user_id=user_id,
            )
        )

        repository.batch_exclude_session_idle_checks.assert_awaited_once_with(
            [first_pair, second_pair, first_pair], user_id
        )

    async def test_include_hands_the_pairs_over_as_named(
        self,
        service: IdleCheckerService,
        repository: MagicMock,
    ) -> None:
        checker_id = IdleCheckerID(uuid4())
        user_id = UserID(uuid4())
        pair = SessionIdleCheckPair(session_id=SessionId(uuid4()), checker_id=checker_id)

        await service.include_sessions(
            IncludeSessionIdleChecksAction(
                targets=[pair],
                user_id=user_id,
            )
        )

        repository.batch_include_session_idle_checks.assert_awaited_once_with([pair], user_id)
