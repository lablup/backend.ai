from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.manager.actions.v2.field.ops import GetFieldOpsAction
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.models.routing.queriers import ModelReplicaQuerier
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupReplicaOwnerAction,
)


@dataclass
class GetReplicaByIdAction(
    GetFieldOpsAction[ReplicaID, DeploymentID, RoutingRow, ModelReplicaData]
):
    """Read one replica, authorized against the deployment it serves."""

    replica_id: ReplicaID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_replica_by_id"

    @override
    def to_owner_lookup_action(self) -> LookupReplicaOwnerAction:
        return LookupReplicaOwnerAction(replica_id=self.replica_id)

    @override
    def to_querier(self) -> ModelReplicaQuerier:
        return ModelReplicaQuerier(replica_id=self.replica_id)
