from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.idle_checker_assignment.actions.base import (
    IdleCheckerAssignmentAction,
)


@dataclass
class AdminSearchIdleCheckerAssignmentsAction(IdleCheckerAssignmentAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class AdminSearchIdleCheckerAssignmentsActionResult(BaseActionResult):
    data: list[IdleCheckerAssignmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
