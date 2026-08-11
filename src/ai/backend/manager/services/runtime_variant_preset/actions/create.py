from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.runtime_variant_preset.actions.base import (
    RuntimeVariantPresetGlobalAction,
)


@dataclass
class CreateRuntimeVariantPresetAction(RuntimeVariantPresetGlobalAction):
    """Add a preset, taking the next rank within its variant.

    Service-kept: the rank is drawn from the presets already stored for the variant,
    which is a read the write spec cannot express.
    """

    creator: Creator[RuntimeVariantPresetRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_runtime_variant_preset"

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
