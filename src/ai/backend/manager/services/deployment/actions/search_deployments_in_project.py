from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentSummaryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.deployment.types import ProjectDeploymentSearchScope
from ai.backend.manager.services.deployment.actions.base import DeploymentScopeAction


@dataclass
class SearchDeploymentsInProjectAction(DeploymentScopeAction):
    """Search deployments within a project scope.

    RBAC validation checks if the user has READ permission in PROJECT scope.
    Used for project admin page.
    """

    scope: ProjectDeploymentSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.scope.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.PROJECT, str(self.scope.project_id))


@dataclass
class SearchDeploymentsInProjectActionResult(BaseActionResult):
    data: list[DeploymentSummaryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
