from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.runtime_variant_preset.actions.base import (
    RuntimeVariantPresetAction,
)


@dataclass
class CreateRuntimeVariantPresetAction(RuntimeVariantPresetAction):
    creator: Creator[RuntimeVariantPresetRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateRuntimeVariantPresetActionResult(BaseActionResult):
    preset: RuntimeVariantPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
