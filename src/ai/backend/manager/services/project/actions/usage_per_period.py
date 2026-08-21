from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class UsagePerPeriodAction(BaseGlobalAction):
    """Aggregate a date range of project resource usage across the installation."""

    start_date: str
    end_date: str
    project_id: UUID | None = None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_project_usage_per_period"


@dataclass(frozen=True)
class UsagePerPeriodActionResult:
    result: list[Any]
