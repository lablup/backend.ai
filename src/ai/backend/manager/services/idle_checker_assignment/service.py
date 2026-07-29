from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
    AdminSearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.create import (
    CreateIdleCheckerAssignmentAction,
    CreateIdleCheckerAssignmentActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.purge import (
    PurgeIdleCheckerAssignmentAction,
    PurgeIdleCheckerAssignmentActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
    ScopedSearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.update import (
    UpdateIdleCheckerAssignmentAction,
    UpdateIdleCheckerAssignmentActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class IdleCheckerAssignmentService:
    _idle_checker_repository: IdleCheckerRepository

    def __init__(self, idle_checker_repository: IdleCheckerRepository) -> None:
        self._idle_checker_repository = idle_checker_repository

    async def create(
        self, action: CreateIdleCheckerAssignmentAction
    ) -> CreateIdleCheckerAssignmentActionResult:
        data = await self._idle_checker_repository.create_assignment(action.creator_spec)
        return CreateIdleCheckerAssignmentActionResult(data=data)

    async def update(
        self, action: UpdateIdleCheckerAssignmentAction
    ) -> UpdateIdleCheckerAssignmentActionResult:
        data = await self._idle_checker_repository.update_assignment(action.updater)
        return UpdateIdleCheckerAssignmentActionResult(data=data)

    async def purge(
        self, action: PurgeIdleCheckerAssignmentAction
    ) -> PurgeIdleCheckerAssignmentActionResult:
        data = await self._idle_checker_repository.purge_assignment(action.purger)
        return PurgeIdleCheckerAssignmentActionResult(data=data)

    async def admin_search(
        self, action: AdminSearchIdleCheckerAssignmentsAction
    ) -> AdminSearchIdleCheckerAssignmentsActionResult:
        result = await self._idle_checker_repository.admin_search_assignments(action.querier)
        return AdminSearchIdleCheckerAssignmentsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def scoped_search(
        self, action: ScopedSearchIdleCheckerAssignmentsAction
    ) -> ScopedSearchIdleCheckerAssignmentsActionResult:
        targets = list(action.targets())
        scopes = [t.to_search_scope() for t in targets]
        result = await self._idle_checker_repository.scoped_search_assignments(
            action.querier, scopes
        )
        return ScopedSearchIdleCheckerAssignmentsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            queried_refs=[t.to_rbac_element_ref() for t in targets],
        )
