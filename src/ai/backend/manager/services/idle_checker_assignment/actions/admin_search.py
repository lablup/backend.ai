from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerAssignmentSearcher


@dataclass(frozen=True)
class AdminSearchIdleCheckerAssignmentsAction(BaseGlobalAction):
    """Page through every binding, whichever scope it hangs on."""

    searcher: IdleCheckerAssignmentSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return IdleCheckerEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_search_idle_checker_assignments"


@dataclass(frozen=True)
class SearchIdleCheckerAssignmentsActionResult:
    items: list[IdleCheckerAssignmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
