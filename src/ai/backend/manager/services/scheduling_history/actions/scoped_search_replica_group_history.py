from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history.types import (
    DeploymentReplicaGroupHistorySearchScope,
    ReplicaGroupReplicaGroupHistorySearchScope,
)


@dataclass(frozen=True)
class ReplicaGroupHistoryTarget(SearchableActionTarget):
    """One scope item of a replica-group scheduling-history search.

    Each variant carries only the id its own dimension is keyed by and derives
    both the row filter and the RBAC element ref from it.
    """


@dataclass(frozen=True)
class ReplicaGroupReplicaGroupHistoryTarget(ReplicaGroupHistoryTarget):
    """Scope item narrowing the history to one replica group.

    Not dispatchable yet: replica groups hold no RBAC permission records of
    their own, so the adapter converts a replica-group scope item into a
    ``DeploymentReplicaGroupHistoryTarget`` on the owning deployment and narrows
    the rows back down with a ``replica_group_id`` query condition. This is the
    target it must pass once virtual scopes land.
    """

    replica_group_id: ReplicaGroupID

    @override
    def to_search_scope(self) -> SearchScope:
        return ReplicaGroupReplicaGroupHistorySearchScope(replica_group_id=self.replica_group_id)

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        # Not dispatchable yet: a replica group is not an RBAC scope of its own, so
        # the adapter never passes this target (it converts to the owning
        # deployment). Once virtual scopes make replica groups a scope, return
        # RBACElementRef(RBACElementType.REPLICA_GROUP, ...).
        raise NotImplementedError(
            "ReplicaGroupReplicaGroupHistoryTarget is not authorizable until replica "
            "groups become RBAC scopes"
        )


@dataclass(frozen=True)
class DeploymentReplicaGroupHistoryTarget(ReplicaGroupHistoryTarget):
    """Scope item covering the history of every replica group the deployment owns."""

    deployment_id: DeploymentID

    @override
    def to_search_scope(self) -> SearchScope:
        return DeploymentReplicaGroupHistorySearchScope(deployment_id=self.deployment_id)

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.MODEL_DEPLOYMENT,
            element_id=str(self.deployment_id),
        )


@dataclass
class ScopedSearchReplicaGroupHistoryAction(BaseScopeAction):
    """Action to search replica-group scheduling history under one scope item."""

    # TODO: Widen to a list of targets once this becomes a bulk action; the scope
    # input already accepts several items and means them to be OR'd, but a
    # BaseScopeAction authorizes exactly one target.
    target: ReplicaGroupHistoryTarget
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
        # TODO: Derive from the target once a ReplicaGroupReplicaGroupHistoryTarget
        # becomes dispatchable; the deployment is the only scope a caller can reach
        # today.
        return ScopeType.MODEL_DEPLOYMENT

    @override
    def scope_id(self) -> str:
        return self.target.to_rbac_element_ref().element_id

    @override
    def target_element(self) -> RBACElementRef:
        return self.target.to_rbac_element_ref()


@dataclass
class ScopedSearchReplicaGroupHistoryActionResult(BaseScopeActionResult):
    """Result of searching replica-group scheduling history under one scope item."""

    items: list[ReplicaGroupHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    target: ReplicaGroupHistoryTarget

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.MODEL_DEPLOYMENT

    @override
    def scope_id(self) -> str:
        return self.target.to_rbac_element_ref().element_id
