"""Database source for app config fragment repository operations."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
    AppConfigFragmentWriteNotAllowed,
)
from ai.backend.manager.models.app_config_allow_list.conditions import (
    AppConfigAllowListConditions,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    ExistsQuerier,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.base.creator import NextValuePolicy
from ai.backend.manager.repositories.ops import DBOpsProvider, WriteOps

__all__ = ("AppConfigFragmentDBSource",)

# Gap between successive ranks, leaving room to re-order fragments without renumbering.
RANK_GAP = 100

app_config_fragment_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.DB_SOURCE,
                layer=LayerType.APP_CONFIG_FRAGMENT_DB_SOURCE,
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


class AppConfigFragmentDBSource:
    """Database source for app config fragment operations."""

    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def _ensure_write_allowed(
        self, w: WriteOps, config_name: str, scope_type: AppConfigScopeType
    ) -> None:
        """Reject the write unless an allow-list row exists for ``(config_name, scope_type)``.

        Runs inside the caller's write transaction (``WriteOps`` is read-capable), so the
        gate check and the write commit atomically — no check-then-write race. Because an
        allow-list row requires a registered ``config_name`` (FK), this also enforces
        registration.
        """
        allowed = await w.exists(
            ExistsQuerier(
                row_class=AppConfigAllowListRow,
                conditions=[
                    AppConfigAllowListConditions.by_config_name_equals(
                        StringMatchSpec(config_name, case_insensitive=False, negated=False)
                    ),
                    AppConfigAllowListConditions.by_scope_type_equals(scope_type),
                ],
            )
        )
        if not allowed:
            raise AppConfigFragmentWriteNotAllowed(
                f"Writing app config {config_name!r} at scope {scope_type.value!r} is not allowed."
            )

    @app_config_fragment_db_source_resilience.apply()
    async def create(self, spec: AppConfigFragmentCreatorSpec) -> AppConfigFragmentData:
        policy = NextValuePolicy(
            column=AppConfigFragmentRow.rank,
            scope_condition=lambda: AppConfigFragmentRow.config_name == spec.config_name,
            lock_selector=sa.select(AppConfigDefinitionRow).where(
                AppConfigDefinitionRow.config_name == spec.config_name
            ),
            gap=RANK_GAP,
        )
        async with self._ops.write_ops() as w:
            await self._ensure_write_allowed(w, spec.config_name, spec.scope_type)
            created = await w.create_with_next_value(policy, spec)
            return created.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        async with self._ops.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigFragmentRow, pk_value=fragment_id))
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData:
        async with self._ops.write_ops() as w:
            existing = await w.query(
                Querier(row_class=AppConfigFragmentRow, pk_value=updater.pk_value)
            )
            if existing is None:
                raise AppConfigFragmentNotFound(f"App config fragment {updater.pk_value} not found")
            await self._ensure_write_allowed(w, existing.row.config_name, existing.row.scope_type)
            result = await w.update(updater)
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {updater.pk_value} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigFragmentRow]) -> AppConfigFragmentData:
        async with self._ops.write_ops() as w:
            existing = await w.query(
                Querier(row_class=AppConfigFragmentRow, pk_value=purger.pk_value)
            )
            if existing is None:
                raise AppConfigFragmentNotFound(f"App config fragment {purger.pk_value} not found")
            await self._ensure_write_allowed(w, existing.row.config_name, existing.row.scope_type)
            result = await w.purge(purger)
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {purger.pk_value} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def admin_search(self, querier: BatchQuerier) -> AppConfigFragmentSearchResult:
        """Superadmin/internal path: query across all fragments with no scope filter."""
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigFragmentRow), querier)
            return AppConfigFragmentSearchResult(
                items=[row.AppConfigFragmentRow.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    @app_config_fragment_db_source_resilience.apply()
    async def scoped_search(
        self,
        querier: BatchQuerier,
        scopes: Sequence[SearchScope],
    ) -> AppConfigFragmentSearchResult:
        """Scoped path: query fragments restricted to ``scopes`` (combined with OR)."""
        async with self._ops.read_ops() as r:
            result = await r.batch_query_with_scopes(
                sa.select(AppConfigFragmentRow), querier, scopes
            )
            return AppConfigFragmentSearchResult(
                items=[row.AppConfigFragmentRow.to_data() for row in result.rows],
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
