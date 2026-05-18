from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.deployment.types import UserDeploymentSearchScope
from ai.backend.manager.services.deployment.actions.base import DeploymentScopeAction


@dataclass(frozen=True)
class SearchUserDeploymentsAction(DeploymentScopeAction):
    """Search deployments created by a specific user.

    Internal name uses the ``User`` scope semantics; the v2 adapter exposes
    this as the user-facing ``my_search`` operation, resolving the current
    user before constructing the scope.
    """

    scope: UserDeploymentSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.scope.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.scope.user_id),
        )


@dataclass(frozen=True)
class SearchUserDeploymentsActionResult(BaseActionResult):
    data: list[ModelDeploymentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
