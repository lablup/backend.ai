from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import (
    DEPLOYMENT_ENTITY_TYPE,
    DEPLOYMENT_SCOPE_TYPE,
    DeploymentID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.scope.target import SearchableScopeTarget
from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history.types import (
    DeploymentReplicaGroupHistoryOperationScope,
)


@dataclass(frozen=True)
class ReplicaGroupHistoryTarget(SearchableScopeTarget):
    """One scope item of a replica-group scheduling-history search.

    Each variant carries only the id its own dimension is keyed by and derives
    both the row filter and the scope it is answered for from it.
    """


@dataclass(frozen=True)
class DeploymentReplicaGroupHistoryTarget(ReplicaGroupHistoryTarget):
    """Scope item covering the history of every replica group the deployment owns."""

    deployment_id: DeploymentID

    @override
    def to_search_scope(self) -> OperationScope:
        return DeploymentReplicaGroupHistoryOperationScope(deployment_id=self.deployment_id)

    @override
    def to_scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=DEPLOYMENT_SCOPE_TYPE, scope_id=self.deployment_id)


@dataclass
class ScopedSearchReplicaGroupHistoryAction(BaseScopeAction):
    """Action to search replica-group scheduling history under one scope item."""

    # TODO: Widen to a list of targets once this becomes a bulk action; the scope
    # input already accepts several items and means them to be OR'd, but a
    # BaseScopeAction authorizes exactly one target.
    target: ReplicaGroupHistoryTarget
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.target.to_scope_ref(),)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_replica_group_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ScopedSearchReplicaGroupHistoryActionResult(BaseScopeActionResult):
    """Result of searching replica-group scheduling history under one scope item."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()

    items: list[ReplicaGroupHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    target: ReplicaGroupHistoryTarget
