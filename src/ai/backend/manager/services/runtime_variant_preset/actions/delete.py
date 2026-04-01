from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.services.runtime_variant_preset.actions.base import (
    RuntimeVariantPresetAction,
)


@dataclass
class DeleteRuntimeVariantPresetAction(RuntimeVariantPresetAction):
    id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteRuntimeVariantPresetActionResult(BaseActionResult):
    preset: RuntimeVariantPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
