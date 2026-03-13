from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier

from .base import NotificationChannelScopeAction, NotificationChannelScopeActionResult


@dataclass
class SearchChannelsAction(NotificationChannelScopeAction):
    """Action to search notification channels."""

    querier: BatchQuerier

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
        return RBACElementRef(RBACElementType.GLOBAL, "*")


@dataclass
class SearchChannelsActionResult(NotificationChannelScopeActionResult):
    """Result of searching notification channels."""

    channels: list[NotificationChannelData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return "*"
