from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.user.types import BulkUserCreateResultData, UserCreateResultData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class CreateUserAction(UserAction):
    creator: Creator[UserRow]
    group_ids: list[str] | None = None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateUserActionResult(BaseActionResult):
    data: UserCreateResultData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.user.id)


@dataclass
class BulkUserCreateItem:
    """Individual user creation item for bulk operations."""

    creator: Creator[UserRow]
    group_ids: list[str] | None = None


@dataclass
class BulkCreateUserAction(UserAction):
    """Action for bulk creating multiple users."""

    items: list[BulkUserCreateItem]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "bulk_create"


@dataclass
class BulkCreateUserActionResult(BaseActionResult):
    """Result of bulk user creation."""

    data: BulkUserCreateResultData

    @override
    def entity_id(self) -> str | None:
        return None
