"""Database source for app config fragment repository operations."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentBulkItemError,
    AppConfigFragmentBulkWriteResult,
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
    AppConfigFragmentWriteNotAllowed,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_fragment.conditions import AppConfigFragmentConditions
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.app_config_fragment.types import (
    AppConfigResolveScope,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkConditionalCreator,
    BulkConditionalPurger,
    BulkConditionalUpdater,
    Creator,
    ExistsQuerier,
    NoPagination,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider, WriteOps

__all__ = ("AppConfigFragmentDBSource",)

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

    async def _update_in_tx(
        self,
        w: WriteOps,
        updater: Updater[AppConfigFragmentRow],
        only_if: ExistsQuerier[AppConfigAllowListRow],
    ) -> AppConfigFragmentData:
        """Gate + update one fragment inside the caller's write transaction.

        A missing fragment surfaces as the update returning None below.
        """
        if not await w.exists(only_if):
            raise AppConfigFragmentWriteNotAllowed(
                f"Writing app config fragment {updater.pk_value} is not allowed."
            )
        result = await w.update(updater)
        if result is None:
            raise AppConfigFragmentNotFound(f"App config fragment {updater.pk_value} not found")
        return result.row.to_data()

    async def _purge_in_tx(
        self,
        w: WriteOps,
        purger: Purger[AppConfigFragmentRow],
        only_if: ExistsQuerier[AppConfigAllowListRow],
    ) -> AppConfigFragmentData:
        """Gate + purge one fragment inside the caller's write transaction.

        A missing fragment surfaces as the purge returning None below.
        """
        if not await w.exists(only_if):
            raise AppConfigFragmentWriteNotAllowed(
                f"Writing app config fragment {purger.pk_value} is not allowed."
            )
        result = await w.purge(purger)
        if result is None:
            raise AppConfigFragmentNotFound(f"App config fragment {purger.pk_value} not found")
        return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def create(
        self,
        spec: AppConfigFragmentCreatorSpec,
        only_if: ExistsQuerier[AppConfigAllowListRow],
    ) -> AppConfigFragmentData:
        """Gate + create one fragment in a single write transaction.

        The gate check and the write run in one transaction, so they commit atomically —
        no check-then-write race. ``rank`` is derived from the fragment's ``scope_type``.
        """
        async with self._ops.write_ops() as w:
            if not await w.exists(only_if):
                raise AppConfigFragmentWriteNotAllowed(
                    f"Writing app config {spec.config_name!r} at scope "
                    f"{spec.scope_type.value!r} is not allowed."
                )
            created = await w.create(Creator(spec=spec))
            return created.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        async with self._ops.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigFragmentRow, pk_value=fragment_id))
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def update(
        self,
        updater: Updater[AppConfigFragmentRow],
        only_if: ExistsQuerier[AppConfigAllowListRow],
    ) -> AppConfigFragmentData:
        async with self._ops.write_ops() as w:
            return await self._update_in_tx(w, updater, only_if)

    @app_config_fragment_db_source_resilience.apply()
    async def purge(
        self,
        purger: Purger[AppConfigFragmentRow],
        only_if: ExistsQuerier[AppConfigAllowListRow],
    ) -> AppConfigFragmentData:
        async with self._ops.write_ops() as w:
            return await self._purge_in_tx(w, purger, only_if)

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_create(
        self,
        bulk: BulkConditionalCreator[AppConfigFragmentRow, AppConfigAllowListRow],
    ) -> AppConfigFragmentBulkWriteResult:
        """Create many fragments with partial success.

        Each item is gated and inserted independently in its own savepoint: a rejected gate or a
        failed insert is reported in ``failed`` (with its batch index) while the rest are
        created. The whole batch shares one transaction, so the successful inserts commit together.
        """
        async with self._ops.write_ops() as w:
            result = await w.bulk_conditional_create_partial(bulk)
            return AppConfigFragmentBulkWriteResult(
                succeeded=[row.to_data() for row in result.successes],
                failed=[
                    AppConfigFragmentBulkItemError(index=e.index, message=str(e.exception))
                    for e in result.errors
                ],
            )

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_update(
        self,
        bulk: BulkConditionalUpdater[AppConfigFragmentRow, AppConfigAllowListRow],
    ) -> AppConfigFragmentBulkWriteResult:
        """Update many fragments with partial success.

        Each item is gated and updated independently in its own savepoint: a rejected gate, a
        missing target, or a failed update is reported in ``failed`` while the rest are updated.
        """
        async with self._ops.write_ops() as w:
            result = await w.bulk_conditional_update_partial(bulk)
            return AppConfigFragmentBulkWriteResult(
                succeeded=[row.to_data() for row in result.successes],
                failed=[
                    AppConfigFragmentBulkItemError(index=e.index, message=str(e.exception))
                    for e in result.errors
                ],
            )

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_purge(
        self,
        bulk: BulkConditionalPurger[AppConfigFragmentRow, AppConfigAllowListRow],
    ) -> AppConfigFragmentBulkWriteResult:
        """Purge many fragments with partial success.

        Each item is gated and deleted independently in its own savepoint: a rejected gate, a
        missing target, or a failed delete is reported in ``failed`` while the rest are purged.
        """
        async with self._ops.write_ops() as w:
            result = await w.bulk_conditional_purge_partial(bulk)
            return AppConfigFragmentBulkWriteResult(
                succeeded=[row.to_data() for row in result.successes],
                failed=[
                    AppConfigFragmentBulkItemError(index=e.index, message=str(e.exception))
                    for e in result.errors
                ],
            )

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

    @app_config_fragment_db_source_resilience.apply()
    async def list_visible_fragments(
        self, config_name: str, scope: AppConfigResolveScope
    ) -> list[AppConfigFragmentData]:
        """Fragments visible to ``scope`` for ``config_name``, ``rank``-ordered, in one query.

        Filters on the fragment's own ``scope_type``/``scope_id`` columns: the public OR the
        scope's domain OR the scope's user fragment. Each ``(config_name, scope_type,
        scope_id)`` is unique, so the result is bounded (one per scope_type), ready to
        deep-merge in order.
        """
        public = AppConfigFragmentConditions.by_public_visibility(config_name)
        domain = AppConfigFragmentConditions.by_domain_visibility(config_name, str(scope.domain_id))
        user = AppConfigFragmentConditions.by_user_visibility(config_name, str(scope.user_id))
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[lambda: sa.or_(public(), domain(), user())],
            orders=[AppConfigFragmentRow.rank.asc()],
        )
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigFragmentRow), querier)
            return [row.AppConfigFragmentRow.to_data() for row in result.rows]

    @app_config_fragment_db_source_resilience.apply()
    async def list_visible_fragments_bulk(
        self, config_names: list[str], scope: AppConfigResolveScope
    ) -> list[AppConfigFragmentData]:
        """Visible fragments for several ``config_names`` at once, in a single query.

        The bulk form of :meth:`list_visible_fragments`: per name, the public OR the scope's
        domain OR the scope's user fragment. Ordered by ``(config_name, rank)`` so the caller
        can group by name and deep-merge each in order.
        """
        if not config_names:
            return []
        visibility = []
        for config_name in config_names:
            visibility.append(AppConfigFragmentConditions.by_public_visibility(config_name))
            visibility.append(
                AppConfigFragmentConditions.by_domain_visibility(config_name, str(scope.domain_id))
            )
            visibility.append(
                AppConfigFragmentConditions.by_user_visibility(config_name, str(scope.user_id))
            )
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[lambda: sa.or_(*(condition() for condition in visibility))],
            orders=[AppConfigFragmentRow.config_name.asc(), AppConfigFragmentRow.rank.asc()],
        )
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigFragmentRow), querier)
            return [row.AppConfigFragmentRow.to_data() for row in result.rows]

    @app_config_fragment_db_source_resilience.apply()
    async def list_public_fragments(self, config_name: str) -> list[AppConfigFragmentData]:
        """Public fragments of ``config_name``, ``rank``-ordered — the anonymous read view.

        No principal: only ``public``-scope documents contribute, so a pre-login caller sees
        the shared baseline config without any domain or user overlay.
        """
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[AppConfigFragmentConditions.by_public_visibility(config_name)],
            orders=[AppConfigFragmentRow.rank.asc()],
        )
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigFragmentRow), querier)
            return [row.AppConfigFragmentRow.to_data() for row in result.rows]
