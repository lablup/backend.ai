from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.user.types import BulkUserUpdateResultData, UserData
from ai.backend.manager.models.user.updaters import UserUpdater

__all__ = (
    "UpdateUserAction",
    "UpdateUserActionResult",
    "BulkUpdateUserAction",
    "BulkUpdateUserActionResult",
)


@dataclass(frozen=True)
class UpdateUserAction(BaseSingleEntityAction):
    """Edit one user."""

    updater: UserUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_user"


@dataclass(frozen=True)
class UpdateUserActionResult:
    data: UserData


@dataclass(frozen=True)
class BulkUpdateUserAction(BaseGlobalAction):
    """Edit several users at once, across domains."""

    items: list[UserUpdater]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_update_users"


@dataclass(frozen=True)
class BulkUpdateUserActionResult:
    data: BulkUserUpdateResultData
