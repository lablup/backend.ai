from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.queriers import (
    DeploymentPresetQuerier,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow


@dataclass
class GetDeploymentPresetAction(
    GetSingleEntityOpsAction[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Read one deployment revision preset."""

    preset_id: DeploymentPresetID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_deployment_preset"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def to_querier(self) -> DeploymentPresetQuerier:
        return DeploymentPresetQuerier(preset_id=self.preset_id)
