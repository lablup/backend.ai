from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow


@dataclass(frozen=True)
class GlobalSearchReplicaGroupHistoryAction(
    GlobalSearcherOpsAction[ReplicaGroupHistoryRow, ReplicaGroupHistoryData]
):
    """Page through every replica-group history row."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_replica_group_history"
