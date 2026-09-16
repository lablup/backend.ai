from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import ReplicaGroupData
from ai.backend.manager.models.replica_group.queriers import BulkReplicaGroupQuerier
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkReplicaGroupOwnerAction,
)


@dataclass
class BulkGetReplicaGroupsAction(
    PartialBulkGetFieldOpsAction[ReplicaGroupID, DeploymentID, ReplicaGroupRow, ReplicaGroupData]
):
    """Read the replica groups the caller named, answering for each one."""

    ids: Sequence[ReplicaGroupID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_replica_groups"

    @override
    def field_ids(self) -> Sequence[ReplicaGroupID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkReplicaGroupOwnerAction:
        return LookupBulkReplicaGroupOwnerAction(replica_group_ids=self.ids)

    @override
    def to_querier(self) -> BulkReplicaGroupQuerier:
        return BulkReplicaGroupQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[ReplicaGroupID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
