from __future__ import annotations

from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
    AppConfigAllowListSearchResult,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.app_config_allow_list.db_source import (
    AppConfigAllowListDBSource,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, Purger
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigAllowListRepository",)


class AppConfigAllowListRepository:
    """Access to app config allow-list entries."""

    _db_source: AppConfigAllowListDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigAllowListDBSource(ops_provider)

    async def create(
        self,
        creator: Creator[AppConfigAllowListRow],
    ) -> AppConfigAllowListData:
        return await self._db_source.create(creator)

    async def get_by_id(self, allow_list_id: AppConfigAllowListID) -> AppConfigAllowListData:
        return await self._db_source.get_by_id(allow_list_id)

    async def search(self, querier: BatchQuerier) -> AppConfigAllowListSearchResult:
        return await self._db_source.search(querier)

    async def purge(self, purger: Purger[AppConfigAllowListRow]) -> AppConfigAllowListData:
        return await self._db_source.purge(purger)
