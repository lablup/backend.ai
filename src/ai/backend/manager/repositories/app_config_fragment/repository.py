from __future__ import annotations

import uuid

from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.db_source import (
    AppConfigFragmentDBSource,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigData,
    AppConfigFragmentSearchResult,
    AppConfigFragmentSearchScope,
    AppConfigSearchResult,
    UserAppConfigSearchScope,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier


class AppConfigFragmentRepository:
    """Read-side repository for AppConfigFragment.

    Scope-bound reads on raw fragments plus the per-user merged
    `AppConfig` view (BEP-1052 §5). Mutations and admin cross-scope
    reads live on `AppConfigFragmentAdminRepository`.
    """

    _db_source: AppConfigFragmentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigFragmentDBSource(db)

    # ── Raw fragment reads ────────────────────────────────────────

    async def get(self, key: AppConfigFragmentKey) -> AppConfigFragmentData | None:
        return await self._db_source.get(key)

    async def get_by_id(self, id: uuid.UUID) -> AppConfigFragmentData | None:
        return await self._db_source.get_by_id(id)

    async def search(
        self,
        scope: AppConfigFragmentSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.search(scope, querier)

    # ── Merged view (AppConfig) ───────────────────────────────────

    async def app_config(
        self,
        user_id: uuid.UUID,
        config_name: str,
    ) -> AppConfigData:
        return await self._db_source.get_user_app_config(user_id, config_name)

    async def search_app_configs(
        self,
        scope: UserAppConfigSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.search_user_app_configs(scope, querier)
