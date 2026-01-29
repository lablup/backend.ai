from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.actions.base import GroupAction


# TODO: Change to batch action
@dataclass
class UsagePerMonthAction(GroupAction):
    month: str
    group_ids: list[UUID] | None = None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "usage_per_month"


@dataclass
class UsagePerMonthActionResult(BaseActionResult):
    # TODO: Define return type
    result: list[Any]

    @override
    def entity_id(self) -> str | None:
        return None
