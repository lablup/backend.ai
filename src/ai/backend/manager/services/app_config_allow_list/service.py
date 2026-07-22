from __future__ import annotations

from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.services.app_config_allow_list.actions.admin_search import (
    AdminSearchAppConfigAllowListAction,
    SearchAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.create import (
    CreateAppConfigAllowListAction,
    CreateAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.get import (
    GetAppConfigAllowListAction,
    GetAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.purge import (
    PurgeAppConfigAllowListAction,
    PurgeAppConfigAllowListActionResult,
)
from ai.backend.manager.services.app_config_allow_list.actions.update import (
    UpdateAppConfigAllowListAction,
    UpdateAppConfigAllowListActionResult,
)

__all__ = ("AppConfigAllowListService",)


class AppConfigAllowListService:
    _repository: AppConfigAllowListRepository

    def __init__(self, repository: AppConfigAllowListRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateAppConfigAllowListAction
    ) -> CreateAppConfigAllowListActionResult:
        data = await self._repository.create(action.creator)
        return CreateAppConfigAllowListActionResult(allow_list=data)

    async def get(self, action: GetAppConfigAllowListAction) -> GetAppConfigAllowListActionResult:
        data = await self._repository.get_by_id(action.allow_list_id)
        return GetAppConfigAllowListActionResult(allow_list=data)

    async def admin_search(
        self, action: AdminSearchAppConfigAllowListAction
    ) -> SearchAppConfigAllowListActionResult:
        result = await self._repository.admin_search(action.querier)
        return SearchAppConfigAllowListActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def update(
        self, action: UpdateAppConfigAllowListAction
    ) -> UpdateAppConfigAllowListActionResult:
        data = await self._repository.update(action.updater)
        return UpdateAppConfigAllowListActionResult(allow_list=data)

    async def purge(
        self, action: PurgeAppConfigAllowListAction
    ) -> PurgeAppConfigAllowListActionResult:
        data = await self._repository.purge(action.purger)
        return PurgeAppConfigAllowListActionResult(allow_list=data)
