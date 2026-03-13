from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.agent.types import AgentDetailData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier

from .base import AgentScopeAction, AgentScopeActionResult


@dataclass
class SearchAgentsAction(AgentScopeAction):
    querier: BatchQuerier
    _domain_name: str = "*"  # "*" means all domains (superadmin scope)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

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
class SearchAgentsActionResult(AgentScopeActionResult):
    """Result of searching agents with their permissions."""

    agents: list[AgentDetailData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    _domain_name: str = "*"  # "*" means all domains (superadmin scope)

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return "*"
