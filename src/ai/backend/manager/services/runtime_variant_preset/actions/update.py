from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.updaters import RuntimeVariantPresetUpdater


@dataclass
class UpdateRuntimeVariantPresetAction(BaseSingleEntityAction):
    """Change a preset, rejecting combinations the stored row would make invalid.

    Service-kept: the check reads the current row to decide whether the incoming
    partial update lands on a legal pair.
    """

    updater: RuntimeVariantPresetUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_runtime_variant_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.preset_id


@dataclass
class UpdateRuntimeVariantPresetActionResult:
    preset: RuntimeVariantPresetData
