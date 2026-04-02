import logging
from typing import cast

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.runtime_variant_preset.creators import (
    RuntimeVariantPresetCreatorSpec,
)
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
    CreateRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.delete import (
    DeleteRuntimeVariantPresetAction,
    DeleteRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.search import (
    SearchRuntimeVariantPresetsAction,
    SearchRuntimeVariantPresetsActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
    UpdateRuntimeVariantPresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

VALID_PRESET_TARGETS = {"env", "args"}
VALID_VALUE_TYPES = {"str", "int", "float", "bool"}

VALUE_TYPE_VALIDATORS: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
}


def _validate_default_value(default_value: str | None, value_type: str) -> None:
    if default_value is None:
        return
    validator = VALUE_TYPE_VALIDATORS.get(value_type)
    if validator is None:
        return
    if validator is bool:
        if default_value.lower() not in ("true", "false", "1", "0"):
            raise InvalidAPIParameters(
                f"default_value '{default_value}' is not a valid {value_type}"
            )
    else:
        try:
            validator(default_value)
        except (ValueError, TypeError) as e:
            raise InvalidAPIParameters(
                f"default_value '{default_value}' is not a valid {value_type}: {e}"
            ) from e


class RuntimeVariantPresetService:
    _repository: RuntimeVariantPresetRepository

    def __init__(self, repository: RuntimeVariantPresetRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateRuntimeVariantPresetAction
    ) -> CreateRuntimeVariantPresetActionResult:
        spec = cast(RuntimeVariantPresetCreatorSpec, action.creator.spec)

        if spec.preset_target not in VALID_PRESET_TARGETS:
            raise InvalidAPIParameters(
                f"preset_target must be one of {VALID_PRESET_TARGETS}, got '{spec.preset_target}'"
            )
        if spec.value_type not in VALID_VALUE_TYPES:
            raise InvalidAPIParameters(
                f"value_type must be one of {VALID_VALUE_TYPES}, got '{spec.value_type}'"
            )
        _validate_default_value(spec.default_value, spec.value_type)

        next_rank = await self._repository.get_next_rank(spec.runtime_variant_id)
        spec.rank = next_rank

        data = await self._repository.create(action.creator)
        return CreateRuntimeVariantPresetActionResult(preset=data)

    async def update(
        self, action: UpdateRuntimeVariantPresetAction
    ) -> UpdateRuntimeVariantPresetActionResult:
        action.updater.pk_value = action.id
        data = await self._repository.update(action.updater)
        return UpdateRuntimeVariantPresetActionResult(preset=data)

    async def delete(
        self, action: DeleteRuntimeVariantPresetAction
    ) -> DeleteRuntimeVariantPresetActionResult:
        data = await self._repository.delete(action.id)
        return DeleteRuntimeVariantPresetActionResult(preset=data)

    async def search(
        self, action: SearchRuntimeVariantPresetsAction
    ) -> SearchRuntimeVariantPresetsActionResult:
        items, total_count, has_next_page, has_previous_page = await self._repository.search(
            action.querier
        )
        return SearchRuntimeVariantPresetsActionResult(
            items=items,
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )
