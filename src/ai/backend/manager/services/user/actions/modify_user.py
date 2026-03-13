from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import BulkUserUpdateResultData, UserData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.user.actions.base import UserAction, UserSingleEntityAction

if TYPE_CHECKING:
    from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec


@dataclass
class ModifyUserAction(UserSingleEntityAction):
    email: str
    updater: Updater[UserRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        # The email is used to identify the user for modification
        # However, we need the UUID for RBAC. This will be resolved in the processor
        # For now, return email as placeholder - processor will populate actual UUID
        return self.email

    @override
    def target_element(self) -> RBACElementRef:
        # Email-based lookup requires resolution in processor
        # This is a limitation of the current design
        return RBACElementRef(RBACElementType.USER, self.email)


@dataclass
class ModifyUserActionResult(BaseActionResult):
    data: UserData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)

    def target_entity_id(self) -> str:
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
