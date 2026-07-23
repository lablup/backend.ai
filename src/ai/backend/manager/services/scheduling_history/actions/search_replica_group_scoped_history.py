from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchReplicaGroupScopedHistoryAction(BaseScopeAction):
    """Action to search replica-group scheduling history under one deployment.

    The owning deployment is the authorization subject, scope, and target:
    replica groups hold no permission records of their own, so whoever may read
    the deployment may read its replica groups' scheduling history. A
    replica-group-only request resolves its deployment first
    (``ResolveReplicaGroupDeploymentAction``); ``replica_group_id`` then only
    narrows the repository query.
    """

    deployment_id: DeploymentID
    replica_group_id: ReplicaGroupID | None
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.MODEL_DEPLOYMENT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.MODEL_DEPLOYMENT

    @override
    def scope_id(self) -> str:
        return str(self.deployment_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.MODEL_DEPLOYMENT,
            element_id=str(self.deployment_id),
        )


@dataclass
class SearchReplicaGroupScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching replica-group scheduling history within scope."""

    items: list[ReplicaGroupHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    deployment_id: DeploymentID
    replica_group_id: ReplicaGroupID | None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.MODEL_DEPLOYMENT

    @override
    def scope_id(self) -> str:
        return str(self.deployment_id)
