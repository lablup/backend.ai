"""DataQuerier implementations for the deployment revision preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.specs.querier import DataQuerier

__all__ = ("DeploymentPresetQuerier",)


@dataclass
class DeploymentPresetQuerier(
    DataQuerier[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    preset_id: DeploymentPresetID

    @override
    def row_class(self) -> type[DeploymentRevisionPresetRow]:
        return DeploymentRevisionPresetRow

    @override
    def pk_value(self) -> DeploymentPresetID:
        return self.preset_id

    @override
    def to_data(self, row: DeploymentRevisionPresetRow) -> DeploymentRevisionPresetData:
        return row.to_data()
