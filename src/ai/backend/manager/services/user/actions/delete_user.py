from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction

__all__ = ("DeleteUserAction", "DeleteUserActionResult")


@dataclass(frozen=True)
class DeleteUserAction(BaseSingleEntityAction):
    """Retire one user."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_user"


@dataclass(frozen=True)
class DeleteUserActionResult:
    pass
