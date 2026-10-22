import logging

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    VALUE_TYPE_VALIDATORS,
    PresetTarget,
    PresetValueType,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.updaters import RuntimeVariantPresetUpdater
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.services.runtime_variant_preset.actions.partial_bulk_update import (
    PartialBulkUpdateRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
    UpdateRuntimeVariantPresetActionResult,
)

log = StructuredLogger(logging.getLogger(__spec__.name))


class RuntimeVariantPresetService:
    """The preset updates that read before they write.

    Everything else runs straight against ops — the value-type check is what keeps
    these here.
    """

    _repository: RuntimeVariantPresetRepository
    _ops_repository: OpsRepository[RuntimeVariantPresetData]

    def __init__(
        self,
        repository: RuntimeVariantPresetRepository,
        ops_repository: OpsRepository[RuntimeVariantPresetData],
    ) -> None:
        self._repository = repository
        self._ops_repository = ops_repository

    async def update(
        self, action: UpdateRuntimeVariantPresetAction
    ) -> UpdateRuntimeVariantPresetActionResult:
        updater = action.updater
        current = await self._repository.get_by_id(updater.preset_id)
        if (rejection := self._rejection(updater, current)) is not None:
            raise rejection
        data = await self._ops_repository.update(updater)
        return UpdateRuntimeVariantPresetActionResult(preset=data)

    async def partial_bulk_update(
        self, action: PartialBulkUpdateRuntimeVariantPresetsAction
    ) -> PartialBulkResult[RuntimeVariantPresetData]:
        """Update each named preset the check accepts, answering for every one."""
        stored = {
            data.id: data
            for data in await self._repository.get_by_ids([
                updater.preset_id for updater in action.updaters
            ])
        }
        rejected: dict[EntityIdentifier, Exception] = {}
        accepted: dict[EntityIdentifier, RuntimeVariantPresetUpdater] = {}
        for updater in action.updaters:
            current = stored.get(updater.preset_id)
            rejection = self._rejection(updater, current) if current is not None else None
            if rejection is not None:
                rejected[updater.preset_id] = rejection
            else:
                accepted[updater.preset_id] = updater
        result = await self._ops_repository.partial_bulk_update(accepted)
        errors = {**rejected, **result.errors}
        return PartialBulkResult(
            items=[
                PartialBulkEntityResult[RuntimeVariantPresetData].succeeded(
                    updater.preset_id, result.successes[updater.preset_id]
                )
                if updater.preset_id in result.successes
                else PartialBulkEntityResult[RuntimeVariantPresetData].failed(
                    updater.preset_id, errors[updater.preset_id]
                )
                for updater in action.updaters
            ]
        )

    def _rejection(
        self, updater: RuntimeVariantPresetUpdater, current: RuntimeVariantPresetData
    ) -> InvalidAPIParameters | None:
        """The error for an update that would leave the stored row invalid, if any."""
        effective_value_type = updater.value_type.optional_value() or current.value_type
        effective_preset_target = updater.preset_target.optional_value() or current.preset_target
        if (
            effective_value_type == PresetValueType.FLAG
            and effective_preset_target != PresetTarget.ARGS
        ):
            return InvalidAPIParameters(
                "value_type 'flag' is only valid with preset_target 'args'."
            )

        if updater.default_value.is_update():
            new_default_value = updater.default_value.value()
            validator = VALUE_TYPE_VALIDATORS[effective_value_type]
            try:
                validator(new_default_value)
            except (ValueError, TypeError) as e:
                return InvalidAPIParameters(
                    f"default_value '{new_default_value}' is not a valid "
                    f"{effective_value_type}: {e}"
                )
        return None
