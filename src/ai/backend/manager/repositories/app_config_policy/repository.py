from __future__ import annotations

import uuid
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


class AppConfigPolicyRepository:
    """Repository for AppConfigPolicy. Delegates to `AppConfigPolicyDBSource`.

    Public surface:
    - `policy(config_name)` / `policy_by_id(id)` — single lookups.
    - `create / update / purge` — bulk-orchestrated by the service layer.
      The required-policy invariant (BEP-1052 §1) is enforced by the
      service layer; the FK on `app_config_fragments.name` is the
      defense-in-depth backstop.
    - `search(querier)` — paginated cross-policy search.
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigPolicyDBSource(db)

    async def policy(self, config_name: str) -> AppConfigPolicyData | None:
        return await self._db_source.get(config_name)

    async def policy_by_id(self, id: uuid.UUID) -> AppConfigPolicyData | None:
        return await self._db_source.get_by_id(id)

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
