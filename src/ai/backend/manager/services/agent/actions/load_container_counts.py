from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import AgentScopeAction, AgentScopeActionResult


@dataclass
class LoadContainerCountsAction(AgentScopeAction):
    """Action to load container counts."""

    agent_ids: Sequence[AgentId]
    _domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self._domain_name)


@dataclass
class LoadContainerCountsActionResult(AgentScopeActionResult):
    """Result of loading container counts.

    container_counts is in the same order as the input agent_ids.
    """

    container_counts: Sequence[int]
    _domain_name: str

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self._domain_name
