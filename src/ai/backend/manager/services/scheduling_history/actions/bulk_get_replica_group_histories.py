from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group_history import ReplicaGroupHistoryID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.models.replica_group_history.queriers import (
    BulkReplicaGroupHistoryQuerier,
)
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.services.scheduling_history.actions.lookup_owner import (
    LookupBulkReplicaGroupHistoryOwnerAction,
)


@dataclass
class BulkGetReplicaGroupHistoriesAction(
    PartialBulkGetFieldOpsAction[
        ReplicaGroupHistoryID,
        DeploymentID,
        ReplicaGroupHistoryRow,
        ReplicaGroupHistoryData,
    ]
):
    """Read the replica-group history rows the caller named."""

    ids: Sequence[ReplicaGroupHistoryID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_replica_group_histories"

    @override
    def field_ids(self) -> Sequence[ReplicaGroupHistoryID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkReplicaGroupHistoryOwnerAction:
        return LookupBulkReplicaGroupHistoryOwnerAction(history_ids=self.ids)

    @override
    def to_querier(self) -> BulkReplicaGroupHistoryQuerier:
        return BulkReplicaGroupHistoryQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[ReplicaGroupHistoryID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
