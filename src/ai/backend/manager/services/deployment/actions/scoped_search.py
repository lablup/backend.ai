"""Deployment search over the scopes deployments are reachable from."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.ops.base import ScopeItem
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.models.endpoint.scopes import (
    ProjectDeploymentOperationScope,
    UserDeploymentOperationScope,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)

__all__ = (
    "DeploymentScopeItem",
    "ProjectDeploymentScopeItem",
    "ScopedSearchDeploymentsAction",
    "ScopedSearchDeploymentsActionResult",
    "UserDeploymentScopeItem",
)


class DeploymentScopeItem(ScopeItem, ABC):
    """One side a deployment is reachable from."""


@dataclass(frozen=True)
class ProjectDeploymentScopeItem(DeploymentScopeItem):
    """The deployments of one project."""

    project_id: ProjectID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id)

    @override
    def operation_scope(self) -> OperationScope:
        return ProjectDeploymentOperationScope(project_id=self.project_id)


@dataclass(frozen=True)
class UserDeploymentScopeItem(DeploymentScopeItem):
    """The deployments one user created."""

    user_id: UserID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id)

    @override
    def operation_scope(self) -> OperationScope:
        return UserDeploymentOperationScope(user_id=self.user_id)


@dataclass
class ScopedSearchDeploymentsAction(DeploymentScopeAction):
    """Page through the deployments the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[DeploymentScopeItem]
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return [item.scope_ref() for item in self.items]

    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_deployments"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ScopedSearchDeploymentsActionResult(DeploymentScopeActionResult):
    data: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
