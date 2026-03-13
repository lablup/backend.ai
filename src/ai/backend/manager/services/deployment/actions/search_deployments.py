from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import PermissionOperationType, ScopeType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class SearchDeploymentsAction(DeploymentScopeAction):
    querier: BatchQuerier

    @override
    def scope_type(self) -> ScopeType:
        return self.querier.scope.type

    @override
    def scope_id(self) -> UUID:
        return self.querier.scope.id

    @override
    @classmethod
    def permission_operation_type(cls) -> PermissionOperationType:
        return PermissionOperationType.READ


@dataclass
class SearchDeploymentsActionResult(DeploymentScopeActionResult):
    data: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _scope_type: ScopeType
    _scope_id: UUID

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return str(self._scope_id)
