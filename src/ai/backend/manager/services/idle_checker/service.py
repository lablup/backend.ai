from ai.backend.common.data.idle_checker.types import IdleCheckerSpec
from ai.backend.common.exception import PrometheusQueryPresetInvalidLabel
from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult, EntityOpsResult
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.idle_checker.actions.create import CreateIdleCheckerAction
from ai.backend.manager.services.idle_checker.actions.exclude_sessions import (
    ExcludeSessionIdleChecksAction,
    ExcludeSessionIdleChecksActionResult,
)
from ai.backend.manager.services.idle_checker.actions.include_sessions import (
    IncludeSessionIdleChecksAction,
    IncludeSessionIdleChecksActionResult,
)
from ai.backend.manager.services.idle_checker.actions.update import UpdateIdleCheckerAction


class IdleCheckerService:
    """The writes that read a preset before writing, and the two session-list edits.

    The catalog's purge and search run straight against ops.
    """

    _repository: IdleCheckerRepository
    _prometheus_query_preset_repository: PrometheusQueryPresetRepository
    _ops_repository: OpsRepository[IdleCheckerData]

    def __init__(
        self,
        repository: IdleCheckerRepository,
        prometheus_query_preset_repository: PrometheusQueryPresetRepository,
        ops_repository: OpsRepository[IdleCheckerData],
    ) -> None:
        self._repository = repository
        self._prometheus_query_preset_repository = prometheus_query_preset_repository
        self._ops_repository = ops_repository

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

    async def create(
        self, action: CreateIdleCheckerAction
    ) -> CreatedEntityOpsResult[IdleCheckerData]:
        await self._validate_utilization_labels(action.creator.spec)
        return CreatedEntityOpsResult(
            data=await self._ops_repository.create_global_entity(action.to_creator())
        )

    async def update(self, action: UpdateIdleCheckerAction) -> EntityOpsResult[IdleCheckerData]:
        spec = action.updater.spec.optional_value()
        if spec is not None:
            await self._validate_utilization_labels(spec)
        return EntityOpsResult(data=await self._ops_repository.update(action.to_updater()))

    async def exclude_sessions(
        self, action: ExcludeSessionIdleChecksAction
    ) -> ExcludeSessionIdleChecksActionResult:
        batch_result = await self._repository.batch_exclude_session_idle_checks(
            action.targets, action.user_id
        )
        return ExcludeSessionIdleChecksActionResult(results=batch_result.results)

    async def include_sessions(
        self, action: IncludeSessionIdleChecksAction
    ) -> IncludeSessionIdleChecksActionResult:
        batch_result = await self._repository.batch_include_session_idle_checks(
            action.targets, action.user_id
        )
        return IncludeSessionIdleChecksActionResult(results=batch_result.results)
