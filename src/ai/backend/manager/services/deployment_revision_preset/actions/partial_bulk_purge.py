from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.purgers import DeploymentPresetPurger
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow


@dataclass
class PartialBulkPurgeDeploymentPresetsAction(
    PartialBulkPurgeEntityOpsAction[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Remove the named presets, answering for each one."""

    ids: Sequence[DeploymentPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_deployment_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, DeploymentPresetPurger]:
        return {preset_id: DeploymentPresetPurger(preset_id) for preset_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[preset_id for preset_id in self.ids if preset_id in allowed])
