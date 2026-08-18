from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DEPLOYMENT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.searchers import (
    DeploymentPresetSearcher,
)


@dataclass
class GlobalSearchDeploymentPresetsAction(
    SearchGlobalOpsAction[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Page through every deployment revision preset."""

    searcher: DeploymentPresetSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_deployment_presets"

    @override
    def to_searcher(self) -> DeploymentPresetSearcher:
        return self.searcher
