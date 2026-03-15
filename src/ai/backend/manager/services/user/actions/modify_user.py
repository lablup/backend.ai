from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.user.types import BulkUserUpdateResultData, UserData
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.user.actions.base import (
    UserAction,
    UserSingleEntityAction,
    UserSingleEntityActionResult,
)
from ai.backend.manager.services.user.types import UserUpdateSpec


@dataclass
class ModifyUserAction(UserSingleEntityAction):
    email: str  # Still needed for the service layer implementation
    updater: Updater[UserRow]
    user_uuid: UUID | None = None  # Set by API layer for RBAC validation

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        if self.user_uuid is None:
            raise ValueError("user_uuid must be set for RBAC validation")
        return str(self.user_uuid)

    @override
    def target_element(self) -> RBACElementRef:
        if self.user_uuid is None:
            raise ValueError("user_uuid must be set for RBAC validation")
        return RBACElementRef(RBACElementType.USER, str(self.user_uuid))


@dataclass
class ModifyUserActionResult(UserSingleEntityActionResult):
    data: UserData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)


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
