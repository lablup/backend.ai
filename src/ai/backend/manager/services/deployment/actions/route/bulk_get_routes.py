from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import RouteInfo
from ai.backend.manager.models.routing.queriers import BulkRouteQuerier
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkReplicaOwnerAction,
)


@dataclass
class BulkGetRoutesAction(
    PartialBulkGetFieldOpsAction[ReplicaID, DeploymentID, RoutingRow, RouteInfo]
):
    """Read the routes the caller named, answering for each one."""

    ids: Sequence[ReplicaID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_routes"

    @override
    def field_ids(self) -> Sequence[ReplicaID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkReplicaOwnerAction:
        return LookupBulkReplicaOwnerAction(replica_ids=self.ids)

    @override
    def to_querier(self) -> BulkRouteQuerier:
        return BulkRouteQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[ReplicaID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
