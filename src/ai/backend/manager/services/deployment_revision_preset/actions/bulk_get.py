from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.queriers import (
    BulkDeploymentPresetQuerier,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow


@dataclass
class BulkGetDeploymentPresetsAction(
    PartialBulkGetEntityOpsAction[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Read the deployment revision presets the caller named, answering for each id."""

    ids: Sequence[DeploymentPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_deployment_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkDeploymentPresetQuerier:
        return BulkDeploymentPresetQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
