from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.purgers import DeploymentPresetPurger
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow


@dataclass
class PurgeDeploymentPresetAction(
    PurgeEntityOpsAction[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Remove a preset.

    Purge-shaped: the table carries no lifecycle column, so deleting one has always
    been the row leaving the table. Its slot rows go with it by FK cascade.
    """

    preset_id: DeploymentPresetID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_deployment_preset"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def to_purger(self) -> DeploymentPresetPurger:
        return DeploymentPresetPurger(self.preset_id)
