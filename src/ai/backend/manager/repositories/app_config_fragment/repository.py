from __future__ import annotations

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.db_source import (
    AppConfigFragmentDBSource,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base import BatchQuerier
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

    async def update(
        self,
        fragment_id: AppConfigFragmentID,
        spec: AppConfigFragmentUpdaterSpec,
    ) -> AppConfigFragmentData:
        return await self._db_source.update(fragment_id, spec)

    async def purge(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        return await self._db_source.purge(fragment_id)

    async def search(self, querier: BatchQuerier) -> AppConfigFragmentSearchResult:
        return await self._db_source.search(querier)

    async def applicable_fragments(
        self,
        config_name: str,
        domain_id: str,
        user_id: str,
    ) -> list[AppConfigFragmentData]:
        return await self._db_source.applicable_fragments(config_name, domain_id, user_id)
