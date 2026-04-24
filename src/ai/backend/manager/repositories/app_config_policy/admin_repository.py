from __future__ import annotations

from collections.abc import Sequence

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_policy.creators import (
    AppConfigPolicyCreatorSpec,
)
from ai.backend.manager.repositories.app_config_policy.db_source import (
    AppConfigPolicyDBSource,
)
from ai.backend.manager.repositories.app_config_policy.types import (
    AppConfigPolicySearchResult,
)
from ai.backend.manager.repositories.app_config_policy.updaters import (
    AppConfigPolicyUpdaterSpec,
)
from ai.backend.manager.repositories.base.creator import Creator
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

    Mutations are routed through shared Creator / Updater / Purger
    helpers so DB constraint violations surface as typed domain errors
    (e.g., :class:`AppConfigPolicyConflict`). Retry + metric policies
    are applied at the DB-source layer.
    """

    _db_source: AppConfigPolicyDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = AppConfigPolicyDBSource(db)

    async def create(
        self,
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData:
        creator: Creator[AppConfigPolicyRow] = Creator(
            spec=AppConfigPolicyCreatorSpec(
                config_name=config_name,
                scope_sources=scope_sources,
            ),
        )
        return await self._db_source.create(creator)

    async def update(
        self,
        config_name: str,
        scope_sources: Sequence[str],
    ) -> AppConfigPolicyData | None:
        spec = AppConfigPolicyUpdaterSpec(scope_sources=scope_sources)
        return await self._db_source.update(config_name, spec)

    async def purge(self, config_name: str) -> bool:
        return await self._db_source.purge(config_name)

    async def search(self, querier: BatchQuerier) -> AppConfigPolicySearchResult:
        return await self._db_source.search(querier)
