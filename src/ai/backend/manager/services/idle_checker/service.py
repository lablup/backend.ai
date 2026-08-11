from typing import cast

from ai.backend.common.data.idle_checker.types import IdleCheckerSpec
from ai.backend.common.exception import PrometheusQueryPresetInvalidLabel
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerCreatorSpec
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerUpdaterSpec
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.idle_checker.actions.admin_search import (
    AdminSearchIdleCheckersAction,
    SearchIdleCheckersActionResult,
)
from ai.backend.manager.services.idle_checker.actions.create import (
    CreateIdleCheckerAction,
    CreateIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.actions.purge import (
    PurgeIdleCheckerAction,
    PurgeIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.actions.update import (
    UpdateIdleCheckerAction,
    UpdateIdleCheckerActionResult,
)


class IdleCheckerService:
    _repository: IdleCheckerRepository
    _prometheus_query_preset_repository: PrometheusQueryPresetRepository

    def __init__(
        self,
        repository: IdleCheckerRepository,
        prometheus_query_preset_repository: PrometheusQueryPresetRepository,
    ) -> None:
        self._repository = repository
        self._prometheus_query_preset_repository = prometheus_query_preset_repository

    async def _validate_utilization_labels(self, spec: IdleCheckerSpec) -> None:
        """Reject spec labels the referenced preset does not declare as allowed."""
        if spec.utilization is None:
            return
        threshold = spec.utilization.threshold
        preset = await self._prometheus_query_preset_repository.get_by_id(threshold.preset_id)
        if preset.filter_labels:
            invalid = {label.key for label in threshold.filter_labels} - set(preset.filter_labels)
            if invalid:
                raise PrometheusQueryPresetInvalidLabel(
                    f"Invalid filter labels: {sorted(invalid)}. "
                    f"Allowed: {sorted(preset.filter_labels)}"
                )
        if preset.group_labels:
            invalid = set(threshold.group_labels) - set(preset.group_labels)
            if invalid:
                raise PrometheusQueryPresetInvalidLabel(
                    f"Invalid group labels: {sorted(invalid)}. "
                    f"Allowed: {sorted(preset.group_labels)}"
                )

    async def admin_search(
        self,
        action: AdminSearchIdleCheckersAction,
    ) -> SearchIdleCheckersActionResult:
        result = await self._repository.admin_search(action.querier)
        return SearchIdleCheckersActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create(self, action: CreateIdleCheckerAction) -> CreateIdleCheckerActionResult:
        creator_spec = cast(IdleCheckerCreatorSpec, action.creator.spec)
        await self._validate_utilization_labels(creator_spec.spec)
        data = await self._repository.create(action.creator)
        return CreateIdleCheckerActionResult(idle_checker=data)

    async def update(self, action: UpdateIdleCheckerAction) -> UpdateIdleCheckerActionResult:
        updater_spec = cast(IdleCheckerUpdaterSpec, action.updater.spec)
        spec = updater_spec.spec.optional_value()
        if spec is not None:
            await self._validate_utilization_labels(spec)
        data = await self._repository.update(action.updater)
        return UpdateIdleCheckerActionResult(idle_checker=data)

    async def purge(self, action: PurgeIdleCheckerAction) -> PurgeIdleCheckerActionResult:
        data = await self._repository.purge(action.purger)
        return PurgeIdleCheckerActionResult(idle_checker=data)
