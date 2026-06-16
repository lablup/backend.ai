from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentKey,
    AppConfigFragmentSearchResult,
    ScopedAppConfigSearchResult,
)
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.db_source import (
    AppConfigFragmentDBSource,
)
from ai.backend.manager.repositories.app_config_fragment.updaters import (
    AppConfigFragmentUpdaterSpec,
)
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.ops import DBOpsProvider

app_config_fragment_admin_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.APP_CONFIG_FRAGMENT_ADMIN_REPOSITORY,
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=5,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AppConfigFragmentAdminRepository:
    """Admin-only operations on AppConfigFragment.

    All mutations (`create` / `update` / `purge`) and cross-scope
    reads (`admin_search` raw, `admin_search_app_configs` merged)
    live here — read-side scope-bound operations are on
    `AppConfigFragmentRepository`. Authorization is enforced at the
    service layer before reaching either repository.

    Mutations are routed through the shared ops helpers (next-value
    creator / Updater / Purger) so the same execution / resilience
    plumbing applies as in sister repositories.
    """

    _db_source: AppConfigFragmentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: DBOpsProvider) -> None:
        self._db_source = AppConfigFragmentDBSource(db, ops_provider)

    # ── Mutations ─────────────────────────────────────────────────

    @app_config_fragment_admin_repository_resilience.apply()
    async def create(
        self,
        key: AppConfigFragmentKey,
        config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        """Insert a fragment; its `rank` is assigned by next-value
        (``MAX(rank) + gap`` within the `name`) in the DB source."""
        spec = AppConfigFragmentCreatorSpec(
            scope_type=key.scope_type,
            scope_id=key.scope_id,
            name=key.name,
            config=config,
        )
        return await self._db_source.create(spec)

    @app_config_fragment_admin_repository_resilience.apply()
    async def update(
        self,
        key: AppConfigFragmentKey,
        config: Mapping[str, Any],
    ) -> AppConfigFragmentData:
        """Update a fragment by natural key. Resolves the natural key
        to the row's UUID, builds an ``Updater``, and delegates to the
        DB source. Raises :class:`AppConfigFragmentNotFound` when the
        row is missing (or vanishes between resolve and write)."""
        pk_value = await self._db_source.resolve_pk_by_key(key)
        if pk_value is None:
            raise AppConfigFragmentNotFound(
                extra_msg=(
                    f"scope_type={key.scope_type.value!r}, "
                    f"scope_id={key.scope_id!r}, name={key.name!r}"
                ),
            )
        updater: Updater[AppConfigFragmentRow] = Updater(
            spec=AppConfigFragmentUpdaterSpec(config=config),
            pk_value=pk_value,
        )
        return await self._db_source.update(updater)

    @app_config_fragment_admin_repository_resilience.apply()
    async def purge(self, key: AppConfigFragmentKey) -> bool:
        """Delete a fragment by natural key. Resolves the natural key,
        builds a ``Purger``, and delegates to the DB source. Returns
        ``True`` only when a row was actually removed."""
        pk_value = await self._db_source.resolve_pk_by_key(key)
        if pk_value is None:
            return False
        purger: Purger[AppConfigFragmentRow] = Purger(
            row_class=AppConfigFragmentRow,
            pk_value=pk_value,
        )
        return await self._db_source.purge(purger)

    # ── Cross-scope reads ────────────────────────────────────────

    @app_config_fragment_admin_repository_resilience.apply()
    async def admin_search(
        self,
        querier: BatchQuerier,
    ) -> AppConfigFragmentSearchResult:
        return await self._db_source.admin_search(querier)

    @app_config_fragment_admin_repository_resilience.apply()
    async def admin_search_app_configs(
        self,
        querier: BatchQuerier,
    ) -> ScopedAppConfigSearchResult:
        return await self._db_source.admin_search_app_configs(querier)
