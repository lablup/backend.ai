"""Deployment revision preset search over the scopes the type is reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow

__all__ = ("ScopedSearchDeploymentPresetsAction",)


@dataclass(frozen=True)
class ScopedSearchDeploymentPresetsAction(
    ScopedSearchOpsAction[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Page through the deployment revision presets the named scopes reach, combined with OR."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentPresetEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_deployment_presets"
