from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.deployment.types import RouteInfo
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.routing.scopes import DeploymentReplicaTarget
from ai.backend.manager.models.routing.searchers import RouteInfoSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchRoutesAction(BulkScopedSearchOpsAction[RoutingRow, RouteInfo]):
    """Page through the routes of the deployments named, combined with OR.

    Every deployment is authorized before the read runs. A route and a replica are the
    same routing row read two ways, so both share one scope target.
    """

    deployment_ids: Sequence[DeploymentID]
    searcher: RouteInfoSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_routes"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.deployment_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            DeploymentReplicaTarget(deployment_id=deployment_id)
            for deployment_id in self.deployment_ids
        ]

    @override
    def to_searcher(self) -> RouteInfoSearcher:
        return self.searcher
