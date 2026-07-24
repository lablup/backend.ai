from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentHistoryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchDeploymentScopedHistoryAction(BaseScopeAction):
    """Action to search the scheduling history of one deployment.

    The history is the entity being read and the deployment is the scope containing it,
    so the RBAC scope chain authorizes the caller for reading history there.
    """

    deployment_id: DeploymentID
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_HISTORY

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
class SearchDeploymentScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching the scheduling history of one deployment."""

    histories: list[DeploymentHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    deployment_id: DeploymentID

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.MODEL_DEPLOYMENT

    @override
    def scope_id(self) -> str:
        return str(self.deployment_id)
