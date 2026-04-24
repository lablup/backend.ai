from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

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
    """Repository for AppConfigFragment.

    Dual role (BEP-1052 §2):
    1. Raw CRUD on `(scope_type, scope_id, name)` rows.
    2. Merged-view reads (`AppConfig`) that resolve a user's chain by
       joining `app_config_policies` in SQL — see `app_config(...)`,
       `search_app_configs(...)`, and `admin_search_app_configs(...)`.
    """

    _db_source: AppConfigFragmentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigFragmentDBSource(db)

    # ── Raw fragment CRUD ──────────────────────────────────────────

    async def fragment(self, key: AppConfigFragmentKey) -> AppConfigFragmentData | None:
        return await self._db_source.get(key)

    async def fragment_by_id(self, id: uuid.UUID) -> AppConfigFragmentData | None:
        return await self._db_source.get_by_id(id)

    async def create(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        return await self._db_source.create(key, extra_config)

    async def update(
        self,
        key: AppConfigFragmentKey,
        extra_config: Mapping[str, Any],
    ) -> AppConfigFragmentData | None:
        return await self._db_source.update(key, extra_config)

    async def purge(self, key: AppConfigFragmentKey) -> bool:
        return await self._db_source.purge(key)

    async def search(
        self,
        scope: AppConfigFragmentSearchScope,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.search(scope, querier)

    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.admin_search(querier)

    # ── Merged view (AppConfig) — thin delegates to db_source ─────

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

    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> AppConfigSearchResult:
        return await self._db_source.admin_search_app_configs(querier)
