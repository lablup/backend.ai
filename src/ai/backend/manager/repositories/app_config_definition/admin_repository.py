from __future__ import annotations

from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config_definition.types import (
    AppConfigDefinitionData,
    AppConfigDefinitionListResult,
)
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.app_config_definition.db_source import (
    AppConfigDefinitionDBSource,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, Purger
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigDefinitionAdminRepository",)


class AppConfigDefinitionAdminRepository:
    """Admin access to app config definitions."""

    _db_source: AppConfigDefinitionDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigDefinitionDBSource(ops_provider)

    async def create(
        self,
        creator: Creator[AppConfigDefinitionRow],
    ) -> AppConfigDefinitionData:
        return await self._db_source.create(creator)

    async def get_by_id(self, definition_id: AppConfigDefinitionID) -> AppConfigDefinitionData:
        return await self._db_source.get_by_id(definition_id)

    async def search(self, querier: BatchQuerier) -> AppConfigDefinitionListResult:
        return await self._db_source.search(querier)

    async def purge(self, purger: Purger[AppConfigDefinitionRow]) -> AppConfigDefinitionData:
        return await self._db_source.purge(purger)
