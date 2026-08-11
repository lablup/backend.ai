from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.runtime_variant_preset.actions.base import (
    RuntimeVariantPresetGlobalAction,
)


@dataclass
class UpdateRuntimeVariantPresetAction(RuntimeVariantPresetGlobalAction):
    """Change a preset, rejecting combinations the stored row would make invalid.

    Service-kept: the check reads the current row to decide whether the incoming
    partial update lands on a legal pair.
    """

    id: RuntimeVariantPresetID
    updater: Updater[RuntimeVariantPresetRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_runtime_variant_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRuntimeVariantPresetActionResult(BaseActionResult):
    preset: RuntimeVariantPresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
