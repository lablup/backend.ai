import logging

from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    VALUE_TYPE_VALIDATORS,
    PresetTarget,
    PresetValueType,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
    UpdateRuntimeVariantPresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantPresetService:
    """The preset update that reads before it writes.

    Everything else runs straight against ops — the value-type check is what keeps
    this one here.
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
        effective_value_type = updater.value_type.optional_value() or current.value_type
        effective_preset_target = updater.preset_target.optional_value() or current.preset_target
        if (
            effective_value_type == PresetValueType.FLAG
            and effective_preset_target != PresetTarget.ARGS
        ):
            raise InvalidAPIParameters("value_type 'flag' is only valid with preset_target 'args'.")

        if updater.default_value.is_update():
            new_default_value = updater.default_value.value()
            validator = VALUE_TYPE_VALIDATORS[effective_value_type]
            try:
                validator(new_default_value)
            except (ValueError, TypeError) as e:
                raise InvalidAPIParameters(
                    f"default_value '{new_default_value}' is not a valid "
                    f"{effective_value_type}: {e}"
                ) from e

        data = await self._ops_repository.update(updater)
        return UpdateRuntimeVariantPresetActionResult(preset=data)
