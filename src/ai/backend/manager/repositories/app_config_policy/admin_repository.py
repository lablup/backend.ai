from __future__ import annotations

from collections.abc import Sequence

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.db_source import (
    AppConfigPolicyDBSource,
)
from ai.backend.manager.repositories.app_config_policy.types import (
    AppConfigPolicySearchResult,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier


class AppConfigPolicyAdminRepository:
    """Admin-only operations on AppConfigPolicy.

    Mutations (`create` / `update` / `purge`) and cross-policy
    `search` live here — read-side single lookups are on
    `AppConfigPolicyRepository`. Authorization is enforced at the
    service layer before reaching either repository.

    Update keeps `config_name` immutable per BEP-1052 §1; the FK on
    `app_config_fragments.name` is the defense-in-depth backstop for
    purge.
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigPolicyDBSource(db)

    async def create(
        self,
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData:
        return await self._db_source.create(config_name, scope_sources)

    async def update(
        self,
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData | None:
        return await self._db_source.update(config_name, scope_sources)

    async def purge(self, config_name: str) -> bool:
        return await self._db_source.purge(config_name)

    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        return await self._db_source.search(querier)
