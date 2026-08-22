from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction

__all__ = ("UserMonthStatsAction", "UserMonthStatsActionResult")


@dataclass(frozen=True)
class UserMonthStatsAction(BaseSingleEntityAction):
    """Read one user's last-month usage statistics."""

    user_id: UserID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_user_month_stats"


@dataclass(frozen=True)
class UserMonthStatsActionResult:
    stats: list[Any]
