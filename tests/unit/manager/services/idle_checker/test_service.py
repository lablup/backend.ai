from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    MetricLabel,
    SessionLifetimeSpec,
    UtilizationSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.exception import PrometheusQueryPresetInvalidLabel
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.repositories.base import Creator, Updater
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerCreatorSpec
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerUpdaterSpec
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.idle_checker.actions.create import CreateIdleCheckerAction
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
        creator=Creator(
            spec=IdleCheckerCreatorSpec(
                name="test-checker",
                description=None,
                target_session_types=[SessionTypes.INTERACTIVE],
                initial_grace_period_seconds=0,
                spec=spec,
            )
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
            query_template="sum by ({group_by})(backendai_container_utilization{{{labels}}})",
            time_window="5m",
            filter_labels=["container_metric_name", "session_id"],
            group_labels=["session_id", "device"],
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture()
    def repository(self) -> MagicMock:
        repository = MagicMock(spec=IdleCheckerRepository)
        repository.create = AsyncMock()
        repository.update = AsyncMock()
        return repository

    @pytest.fixture()
    def preset_repository(self, preset: PrometheusQueryPresetData) -> MagicMock:
        preset_repository = MagicMock(spec=PrometheusQueryPresetRepository)
        preset_repository.get_by_id = AsyncMock(return_value=preset)
        return preset_repository

    @pytest.fixture()
    def service(
        self,
        repository: MagicMock,
        preset_repository: MagicMock,
    ) -> IdleCheckerService:
        return IdleCheckerService(repository, preset_repository)

    async def test_create_with_allowed_labels_passes(
        self,
        service: IdleCheckerService,
        repository: MagicMock,
    ) -> None:
        spec = _utilization_spec(
            filter_labels={"container_metric_name": "cpu_util"},
            group_labels=["session_id", "device"],
        )

        await service.create(_create_action(spec))

        repository.create.assert_awaited_once()

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
        repository: MagicMock,
        spec: IdleCheckerSpec,
    ) -> None:
        with pytest.raises(PrometheusQueryPresetInvalidLabel):
            await service.create(_create_action(spec))
        repository.create.assert_not_awaited()

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
        repository: MagicMock,
    ) -> None:
        action = UpdateIdleCheckerAction(
            updater=Updater(
                spec=IdleCheckerUpdaterSpec(
                    spec=OptionalState.update(
                        _utilization_spec(filter_labels={"unknown_label": "x"})
                    ),
                ),
                pk_value=uuid4(),
            )
        )

        with pytest.raises(PrometheusQueryPresetInvalidLabel):
            await service.update(action)
        repository.update.assert_not_awaited()

    async def test_update_without_spec_skips_validation(
        self,
        service: IdleCheckerService,
        repository: MagicMock,
        preset_repository: MagicMock,
    ) -> None:
        action = UpdateIdleCheckerAction(
            updater=Updater(
                spec=IdleCheckerUpdaterSpec(name=OptionalState.update("renamed")),
                pk_value=uuid4(),
            )
        )

        await service.update(action)

        preset_repository.get_by_id.assert_not_awaited()
        repository.update.assert_awaited_once()
