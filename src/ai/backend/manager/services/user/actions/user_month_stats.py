from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class UserMonthStatsAction(UserAction):
    user_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class UserMonthStatsActionResult(BaseActionResult):
    stats: list[Any]

    @override
    def entity_id(self) -> str | None:
        return None
