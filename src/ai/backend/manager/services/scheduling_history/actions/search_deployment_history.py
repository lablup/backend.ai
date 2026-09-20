from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.deployment.types import DeploymentHistoryData
from ai.backend.manager.models.scheduling_history.row import DeploymentHistoryRow


@dataclass(frozen=True)
class SearchDeploymentHistoryAction(
    GlobalSearcherOpsAction[DeploymentHistoryRow, DeploymentHistoryData]
):
    """Page through every deployment history row."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_deployment_history"
