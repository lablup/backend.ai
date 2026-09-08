from __future__ import annotations

from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
    SearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.lookup import (
    LookupIdleCheckerAssignmentAction,
    LookupIdleCheckerAssignmentActionResult,
    LookupIdleCheckerAssignmentByPairAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
    ScopedSearchIdleCheckerAssignmentsActionResult,
)


class IdleCheckerAssignmentService:
    """Reads a binding, by its id or by the pair it stands between.

    The writes are the relation operations, which the rbac boundary answers for."""

    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    async def lookup(
        self, action: LookupIdleCheckerAssignmentAction
    ) -> LookupIdleCheckerAssignmentActionResult:
        return LookupIdleCheckerAssignmentActionResult(
            data=await self._repository.get_assignment(action.assignment_id)
        )

    async def lookup_by_pair(
        self, action: LookupIdleCheckerAssignmentByPairAction
    ) -> LookupIdleCheckerAssignmentActionResult:
        return LookupIdleCheckerAssignmentActionResult(
            data=await self._repository.get_assignment_by_pair(action.scope, action.idle_checker_id)
        )

    async def admin_search(
        self, action: AdminSearchIdleCheckerAssignmentsAction
    ) -> SearchIdleCheckerAssignmentsActionResult:
        result = await self._repository.admin_search_assignments(action.searcher)
        return SearchIdleCheckerAssignmentsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search(
        self, action: ScopedSearchIdleCheckerAssignmentsAction
    ) -> ScopedSearchIdleCheckerAssignmentsActionResult:
        result = await self._repository.scoped_search_assignments(
            action.operation_scopes(), action.searcher
        )
        return ScopedSearchIdleCheckerAssignmentsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
