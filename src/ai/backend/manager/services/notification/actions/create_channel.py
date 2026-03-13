from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator

from .base import NotificationChannelScopeAction, NotificationChannelScopeActionResult

if TYPE_CHECKING:
    from ai.backend.manager.models.notification import NotificationChannelRow


@dataclass
class CreateChannelAction(NotificationChannelScopeAction):
    """Action to create a notification channel."""

    creator: RBACEntityCreator[NotificationChannelRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

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
class CreateChannelActionResult(NotificationChannelScopeActionResult):
    """Result of creating a notification channel."""

    channel_data: NotificationChannelData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return "*"
