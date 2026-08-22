import logging
from typing import cast

from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.runtime_variant_preset.creators import (
    RuntimeVariantPresetCreatorSpec,
)
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.repositories.runtime_variant_preset.updaters import (
    RuntimeVariantPresetUpdaterSpec,
)
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
    CreateRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
    UpdateRuntimeVariantPresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantPresetService:
    """The two preset writes that read before they write.

    Everything else runs straight against ops — the rank draw and the value-type check
    are what keep these two here.
    """

    _repository: RuntimeVariantPresetRepository

    def __init__(self, repository: RuntimeVariantPresetRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateRuntimeVariantPresetAction
    ) -> CreateRuntimeVariantPresetActionResult:
        spec = cast(RuntimeVariantPresetCreatorSpec, action.creator.spec)
        next_rank = await self._repository.get_next_rank(spec.runtime_variant_id)
        spec.rank = next_rank

        data = await self._repository.create(action.creator)
        return CreateRuntimeVariantPresetActionResult(preset=data)

    async def update(
        self, action: UpdateRuntimeVariantPresetAction
    ) -> UpdateRuntimeVariantPresetActionResult:
        spec = cast(RuntimeVariantPresetUpdaterSpec, action.updater.spec)
        current = await self._repository.get_by_id(action.id)
        effective_value_type = spec.value_type.optional_value() or current.value_type
        effective_preset_target = spec.preset_target.optional_value() or current.preset_target
        if (
            effective_value_type == PresetValueType.FLAG
            and effective_preset_target != PresetTarget.ARGS
        ):
            raise InvalidAPIParameters("value_type 'flag' is only valid with preset_target 'args'.")

        action.updater.pk_value = action.id
        data = await self._repository.update(action.updater)
        return UpdateRuntimeVariantPresetActionResult(preset=data)
