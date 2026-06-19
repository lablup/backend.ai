from __future__ import annotations

from ai.backend.manager.repositories.app_config_definition.repository import (
    AppConfigDefinitionRepository,
)
from ai.backend.manager.services.app_config_definition.actions.create import (
    CreateAppConfigDefinitionAction,
    CreateAppConfigDefinitionActionResult,
)
from ai.backend.manager.services.app_config_definition.actions.get import (
    GetAppConfigDefinitionAction,
    GetAppConfigDefinitionActionResult,
)
from ai.backend.manager.services.app_config_definition.actions.purge import (
    PurgeAppConfigDefinitionAction,
    PurgeAppConfigDefinitionActionResult,
)
from ai.backend.manager.services.app_config_definition.actions.search import (
    SearchAppConfigDefinitionsAction,
    SearchAppConfigDefinitionsActionResult,
)

__all__ = ("AppConfigDefinitionService",)


class AppConfigDefinitionService:
    _repository: AppConfigDefinitionRepository

    def __init__(self, repository: AppConfigDefinitionRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateAppConfigDefinitionAction
    ) -> CreateAppConfigDefinitionActionResult:
        data = await self._repository.create(action.creator)
        return CreateAppConfigDefinitionActionResult(definition=data)

    async def get(self, action: GetAppConfigDefinitionAction) -> GetAppConfigDefinitionActionResult:
        data = await self._repository.get_by_id(action.definition_id)
        return GetAppConfigDefinitionActionResult(definition=data)

    async def search(
        self, action: SearchAppConfigDefinitionsAction
    ) -> SearchAppConfigDefinitionsActionResult:
        result = await self._repository.search(action.querier)
        return SearchAppConfigDefinitionsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def purge(
        self, action: PurgeAppConfigDefinitionAction
    ) -> PurgeAppConfigDefinitionActionResult:
        data = await self._repository.purge(action.purger)
        return PurgeAppConfigDefinitionActionResult(definition=data)
