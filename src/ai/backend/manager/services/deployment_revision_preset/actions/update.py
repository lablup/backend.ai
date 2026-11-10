from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.creators import (
    PresetResourceSlotCreator,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.updaters import DeploymentPresetUpdater


@dataclass
class UpdateDeploymentPresetAction(
    UpdateSingleEntityOpsAction[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Retune a preset, optionally restating the slot quantities it declares.

    ``slot_creators`` of ``None`` leaves the slots alone; a sequence replaces the whole
    set, because a preset states its resources as one thing.
    """

    updater: DeploymentPresetUpdater
    slot_creators: Sequence[PresetResourceSlotCreator] | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_deployment_preset"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @property
    def preset_id(self) -> DeploymentPresetID:
        return self.updater.preset_id

    @override
    def to_updater(self) -> DeploymentPresetUpdater:
        return self.updater
