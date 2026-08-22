from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction

__all__ = ("AdminMonthStatsAction", "AdminMonthStatsActionResult")


@dataclass(frozen=True)
class AdminMonthStatsAction(BaseGlobalAction):
    """Read last-month usage statistics across every user."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_get_user_month_stats"


@dataclass(frozen=True)
class AdminMonthStatsActionResult:
    stats: list[Any]
