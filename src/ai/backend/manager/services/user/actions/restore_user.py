from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction

__all__ = ("RestoreUserAction", "RestoreUserActionResult")


@dataclass(frozen=True)
class RestoreUserAction(BaseSingleEntityAction):
    """Put one retired user back in service."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_user"


@dataclass(frozen=True)
class RestoreUserActionResult:
    pass
