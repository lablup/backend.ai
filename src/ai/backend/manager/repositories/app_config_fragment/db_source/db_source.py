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
    AppConfigFragmentBulkResult,
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.errors.app_config import (
    AppConfigFragmentNotFound,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkCreator,
    Creator,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

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

    @app_config_fragment_db_source_resilience.apply()
    async def create(self, creator: Creator[AppConfigFragmentRow]) -> AppConfigFragmentData:
        # The FK to the allow-list is the gate: inserting a fragment with no
        # allow-list row for its ``(config_name, scope_type)`` raises
        # ``AppConfigFragmentWriteNotAllowed`` (see the spec's integrity checks).
        async with self._ops.write_ops() as w:
            created = await w.create(creator)
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
        # No write-gate here: the FK to the allow-list guarantees a fragment row exists
        # only while its ``(config_name, scope_type)`` entry does, so an existing
        # fragment is always writable at its own scope.
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {updater.pk_value} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigFragmentRow]) -> AppConfigFragmentData:
        # No write-gate here — see ``update``.
        async with self._ops.write_ops() as w:
            result = await w.purge(purger)
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {purger.pk_value} not found")
            return result.row.to_data()

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_create(
        self,
        bulk_creator: BulkCreator[AppConfigFragmentRow],
    ) -> AppConfigFragmentBulkResult:
        """Create many fragments with per-item partial success."""
        async with self._ops.write_ops() as w:
            result = await w.bulk_create_partial(bulk_creator)
            return AppConfigFragmentBulkResult(
                succeeded=[row.to_data() for row in result.successes],
                failed=[
                    AppConfigFragmentBulkItemError(index=error.index, message=str(error.exception))
                    for error in result.errors
                ],
            )

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_update(
        self,
        updaters: Sequence[Updater[AppConfigFragmentRow]],
    ) -> AppConfigFragmentBulkResult:
        """Update many fragments with per-item partial success."""
        async with self._ops.write_ops() as w:
            result = await w.bulk_update_partial(updaters)
            succeeded = [row.to_data() for row in result.successes]
            succeeded_ids = {data.id for data in succeeded}
            errors_by_index = {e.index: str(e.exception) for e in result.errors}
            # A missing PK is skipped by the partial op (no row, no error); report as not-found.
            failed = [
                AppConfigFragmentBulkItemError(
                    index=index,
                    message=errors_by_index.get(
                        index, f"App config fragment {updater.pk_value} not found"
                    ),
                )
                for index, updater in enumerate(updaters)
                if index in errors_by_index or updater.pk_value not in succeeded_ids
            ]
            return AppConfigFragmentBulkResult(succeeded=succeeded, failed=failed)

    @app_config_fragment_db_source_resilience.apply()
    async def bulk_purge(
        self,
        purgers: Sequence[Purger[AppConfigFragmentRow]],
    ) -> AppConfigFragmentBulkResult:
        """Purge many fragments with per-item partial success."""
        async with self._ops.write_ops() as w:
            result = await w.bulk_purge_partial(list(purgers))
            succeeded = [row.to_data() for row in result.successes]
            succeeded_ids = {data.id for data in succeeded}
            errors_by_index = {e.index: str(e.exception) for e in result.errors}
            # A missing PK is skipped by the partial op (no row, no error); report as not-found.
            failed = [
                AppConfigFragmentBulkItemError(
                    index=index,
                    message=errors_by_index.get(
                        index, f"App config fragment {purger.pk_value} not found"
                    ),
                )
                for index, purger in enumerate(purgers)
                if index in errors_by_index or purger.pk_value not in succeeded_ids
            ]
            return AppConfigFragmentBulkResult(succeeded=succeeded, failed=failed)

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
