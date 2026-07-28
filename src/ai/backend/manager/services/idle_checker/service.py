from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.services.idle_checker.actions.admin_search import (
    AdminSearchIdleCheckersAction,
    SearchIdleCheckersActionResult,
)
from ai.backend.manager.services.idle_checker.actions.create import (
    CreateIdleCheckerAction,
    CreateIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.actions.purge import (
    PurgeIdleCheckerAction,
    PurgeIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.actions.update import (
    UpdateIdleCheckerAction,
    UpdateIdleCheckerActionResult,
)


class IdleCheckerService:
    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    async def admin_search(
        self,
        action: AdminSearchIdleCheckersAction,
    ) -> SearchIdleCheckersActionResult:
        result = await self._repository.admin_search(action.querier)
        return SearchIdleCheckersActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create(self, action: CreateIdleCheckerAction) -> CreateIdleCheckerActionResult:
        data = await self._repository.create(action.creator)
        return CreateIdleCheckerActionResult(idle_checker=data)

    async def update(self, action: UpdateIdleCheckerAction) -> UpdateIdleCheckerActionResult:
        data = await self._repository.update(action.updater)
        return UpdateIdleCheckerActionResult(idle_checker=data)

    async def purge(self, action: PurgeIdleCheckerAction) -> PurgeIdleCheckerActionResult:
        data = await self._repository.purge(action.purger)
        return PurgeIdleCheckerActionResult(idle_checker=data)
