from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.db_source import (
    AppConfigFragmentDBSource,
)
from ai.backend.manager.repositories.base import BatchQuerier, Purger, SearchScope, Updater
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigFragmentRepository",)


class AppConfigFragmentRepository:
    """Access to app config fragments."""

    _db_source: AppConfigFragmentDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigFragmentDBSource(ops_provider)

    async def create(self, spec: AppConfigFragmentCreatorSpec) -> AppConfigFragmentData:
        return await self._db_source.create(spec)

    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        return await self._db_source.get_by_id(fragment_id)

    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData:
        return await self._db_source.update(updater)

    async def purge(self, purger: Purger[AppConfigFragmentRow]) -> AppConfigFragmentData:
        return await self._db_source.purge(purger)

    async def admin_search(self, querier: BatchQuerier) -> AppConfigFragmentSearchResult:
        return await self._db_source.admin_search(querier)

    async def scoped_search(
        self, querier: BatchQuerier, scopes: Sequence[SearchScope]
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.scoped_search(querier, scopes)
