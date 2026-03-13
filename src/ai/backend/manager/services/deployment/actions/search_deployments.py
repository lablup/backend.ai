from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import OperationType, RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentScopeAction,
    DeploymentScopeActionResult,
)


@dataclass
class SearchDeploymentsAction(DeploymentScopeAction):
    querier: BatchQuerier
    _scope_type: ScopeType = ScopeType.DOMAIN
    _scope_id: str = ""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id

    @override
    def target_element(self) -> RBACElementRef:
        # Map ScopeType to RBACElementType
        element_type_map = {
            ScopeType.DOMAIN: RBACElementType.DOMAIN,
            ScopeType.PROJECT: RBACElementType.PROJECT,
        }
        element_type = element_type_map.get(self._scope_type, RBACElementType.DOMAIN)
        return RBACElementRef(element_type, self._scope_id)


@dataclass
class SearchDeploymentsActionResult(DeploymentScopeActionResult):
    data: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _scope_type: ScopeType = ScopeType.DOMAIN
    _scope_id: str = ""

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id
