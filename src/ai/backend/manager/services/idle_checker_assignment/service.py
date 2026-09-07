from __future__ import annotations

from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
    SearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.create import (
    CreateIdleCheckerAssignmentAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.lookup import (
    LookupIdleCheckerAssignmentAction,
    LookupIdleCheckerAssignmentActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.purge import (
    PurgeIdleCheckerAssignmentAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
    ScopedSearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.update import (
    DisableIdleCheckerAssignmentAction,
    EnableIdleCheckerAssignmentAction,
)


class IdleCheckerAssignmentService:
    """Hands each relation action's pair to the repository; nothing reads before writing."""

    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    async def lookup(
        self, action: LookupIdleCheckerAssignmentAction
    ) -> LookupIdleCheckerAssignmentActionResult:
        return LookupIdleCheckerAssignmentActionResult(
            data=await self._repository.get_assignment(action.assignment_id)
        )

    async def create(self, action: CreateIdleCheckerAssignmentAction) -> IdleCheckerAssignmentData:
        return await self._repository.create_assignment(
            action.creator, action.scope, action.idle_checker_id
        )

    async def enable(self, action: EnableIdleCheckerAssignmentAction) -> IdleCheckerAssignmentData:
        return await self._repository.enable_assignment(action.scope, action.idle_checker_id)

    async def disable(
        self, action: DisableIdleCheckerAssignmentAction
    ) -> IdleCheckerAssignmentData:
        return await self._repository.disable_assignment(action.scope, action.idle_checker_id)

    async def purge(self, action: PurgeIdleCheckerAssignmentAction) -> None:
        await self._repository.purge_assignment(action.scope, action.idle_checker_id)

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
