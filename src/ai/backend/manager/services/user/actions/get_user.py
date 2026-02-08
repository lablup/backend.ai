from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class GetUserAction(UserAction):
    """Action to retrieve a single user by UUID."""

    user_uuid: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetUserActionResult(BaseActionResult):
    """Result of GetUserAction containing user data."""

    user: UserData

    @override
    def entity_id(self) -> str | None:
        return str(self.user.uuid)
