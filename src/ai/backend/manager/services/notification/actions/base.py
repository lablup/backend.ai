from abc import abstractmethod
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData
from ai.backend.manager.actions.types import ActionOperationType


@dataclass
class NotificationAction(BaseAction):
    """Base action class for notification operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.NOTIFICATION

    @abstractmethod
    @override
    def entity_id(self) -> str | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        raise NotImplementedError


class NotificationChannelScopeAction(BaseScopeAction):
    """Base action class for notification channel scope-based operations (create, search)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.NOTIFICATION_CHANNEL


class NotificationChannelScopeActionResult(BaseScopeActionResult):
    pass


class NotificationChannelSingleEntityAction(BaseSingleEntityAction):
    """Base action class for notification channel single-entity operations (get, update, delete, purge)."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.NOTIFICATION_CHANNEL

    @override
    def field_data(self) -> FieldData | None:
        return None


class NotificationChannelSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
