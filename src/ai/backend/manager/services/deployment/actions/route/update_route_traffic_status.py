"""Action for updating route traffic status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.data.deployment.types import RouteInfo, RouteTrafficStatus
from ai.backend.manager.services.deployment.actions.lookup_owner import LookupReplicaOwnerAction


@dataclass
class UpdateRouteTrafficStatusAction(BaseSingleFieldAction[ReplicaID, DeploymentID]):
    """Set one route's traffic status, authorized against the deployment it serves."""

    route_id: ReplicaID
    traffic_status: RouteTrafficStatus

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_route_traffic_status"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def to_owner_lookup_action(self) -> LookupReplicaOwnerAction:
        return LookupReplicaOwnerAction(replica_id=self.route_id)


@dataclass
class UpdateRouteTrafficStatusActionResult:
    """Result of updating route traffic status."""

    route: RouteInfo
