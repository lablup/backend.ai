from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.agent.actions.base import (
    AgentScopeAction,
    AgentScopeActionResult,
)


@dataclass
class GetTotalResourcesAction(AgentScopeAction):
    _domain_name: str = "*"  # "*" means all domains (superadmin scope)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return "*"

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self._domain_name)


@dataclass
class GetTotalResourcesActionResult(AgentScopeActionResult):
    total_resources: TotalResourceData
    _domain_name: str = "*"  # "*" means all domains (superadmin scope)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return "*"
