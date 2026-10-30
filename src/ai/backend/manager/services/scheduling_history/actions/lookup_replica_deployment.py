from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.deployment import DeploymentEntityType, DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerByKeyOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.routing.lookups import ReplicaDeploymentLookup


@dataclass(frozen=True)
class ReplicaIDKey(LookupKey):
    """The replica a request names, which the deployment owning it is read from."""

    replica_id: ReplicaID

    @override
    def kind(self) -> str:
        return "replica_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"replica_id": str(self.replica_id)}


@dataclass
class LookupReplicaDeploymentAction(LookupFieldOwnerByKeyOpsAction[DeploymentID]):
    """Resolve a replica's id into the deployment it serves."""

    replica_id: ReplicaID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_replica_deployment"

    @override
    def lookup_key(self) -> ReplicaIDKey:
        return ReplicaIDKey(replica_id=self.replica_id)

    @override
    def to_owner_lookup(self) -> ReplicaDeploymentLookup:
        return ReplicaDeploymentLookup(replica_id=self.replica_id)
