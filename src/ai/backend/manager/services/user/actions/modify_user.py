from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.user.types import BulkUserUpdateResultData, UserData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.user.actions.base import UserAction

if TYPE_CHECKING:
    from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec


@dataclass
class ModifyUserAction(UserAction):
    email: str
    updater: Updater[UserRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ModifyUserActionResult(BaseActionResult):
    data: UserData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)


@dataclass
class UserUpdateSpec:
    """Specification for updating a single user, including the target user ID."""

    user_id: UUID
    updater_spec: UserUpdaterSpec


@dataclass
class BulkModifyUserAction(UserAction):
    """Action for bulk updating multiple users."""

    items: list[UserUpdateSpec]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class BulkModifyUserActionResult(BaseActionResult):
    """Result of bulk user update."""

    data: BulkUserUpdateResultData

    @override
    def entity_id(self) -> str | None:
        return None
