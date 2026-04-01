from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.user.actions.base import (
    UserAction,
    UserSingleEntityAction,
    UserSingleEntityActionResult,
)


@dataclass
class DeleteUserAction(UserAction):
    email: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteUserActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class DeleteUserByIdAction(UserSingleEntityAction):
    """UUID-based user soft-delete action for Strawberry v2 mutations."""

    user_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.user_id))


@dataclass
class DeleteUserByIdActionResult(UserSingleEntityActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    def target_entity_id(self) -> str:
        return ""
