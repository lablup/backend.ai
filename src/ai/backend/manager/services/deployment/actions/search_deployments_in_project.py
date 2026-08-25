from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentSummaryData
from ai.backend.manager.models.endpoint.scopes import ProjectDeploymentOperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class SearchDeploymentsInProjectAction(DeploymentScopeAction):
    """Search deployments within a project scope.

    RBAC validation checks if the user has READ permission in PROJECT scope.
    Used for project admin page.
    """

    project_id: ProjectID
    scope: ProjectDeploymentOperationScope
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE,)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_deployments_in_project"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchDeploymentsInProjectActionResult(DeploymentScopeActionResult):
    data: list[DeploymentSummaryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
