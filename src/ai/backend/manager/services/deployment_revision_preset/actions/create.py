from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DEPLOYMENT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalWithFieldsOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.models.deployment_revision_preset.creators import (
    DeploymentPresetCreator,
    PresetResourceSlotCreator,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow


@dataclass
class CreateDeploymentPresetAction(
    CreateGlobalWithFieldsOpsAction[
        DeploymentRevisionPresetRow,
        DeploymentRevisionPresetData,
        PresetResourceSlotRow,
        ResourceSlotEntryData,
    ]
):
    """Register a preset together with the slot quantities it declares.

    One action so the preset and its slot rows share a transaction: a preset without
    its slots would ask for resources it never stated.
    """

    creator: DeploymentPresetCreator
    slot_creators: Sequence[PresetResourceSlotCreator]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_deployment_preset"

    @override
    def to_creator(self) -> DeploymentPresetCreator:
        return self.creator

    @override
    def to_field_creators(self) -> Sequence[PresetResourceSlotCreator]:
        return self.slot_creators
