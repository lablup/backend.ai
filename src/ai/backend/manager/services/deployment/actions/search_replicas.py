from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType, DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.routing.scopes import DeploymentReplicaOperationScope
from ai.backend.manager.models.routing.searchers import ModelReplicaSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchReplicasAction(OperationScopeOpsAction[RoutingRow, ModelReplicaData]):
    """Page through the replicas of one deployment.

    The deployment is the scope, so ops applies that condition. Reading every
    deployment's replicas is the global variant, which says so in its shape.
    """

    deployment_id: DeploymentID
    searcher: ModelReplicaSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_replicas"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.deployment_id,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (DeploymentReplicaOperationScope(deployment_id=self.deployment_id),)

    @override
    def to_searcher(self) -> ModelReplicaSearcher:
        return self.searcher
