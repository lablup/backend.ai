"""Database source for app config allow-list repository operations.

Each public method binds its work to a single session through the injected
``DBOpsProvider``. The caller passes in the spec
(``Creator``/``Purger``/``BatchQuerier``) that scopes the operation.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
    AppConfigAllowListSearchResult,
)
from ai.backend.manager.errors.app_config import AppConfigAllowListNotFound
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigAllowListDBSource",)

app_config_allow_list_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.APP_CONFIG_ALLOW_LIST_DB_SOURCE)
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


class AppConfigAllowListDBSource:
    """Database source for app config allow-list operations."""

    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    @app_config_allow_list_db_source_resilience.apply()
    async def create(
        self,
        creator: Creator[AppConfigAllowListRow],
    ) -> AppConfigAllowListData:
        async with self._ops.write_ops() as w:
            created = await w.create(creator)
            return created.row.to_data()

    @app_config_allow_list_db_source_resilience.apply()
    async def get_by_id(self, allow_list_id: AppConfigAllowListID) -> AppConfigAllowListData:
        async with self._ops.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigAllowListRow, pk_value=allow_list_id))
            if result is None:
                raise AppConfigAllowListNotFound(
                    f"App config allow-list entry {allow_list_id} not found"
                )
            return result.row.to_data()

    @app_config_allow_list_db_source_resilience.apply()
    async def update(self, updater: Updater[AppConfigAllowListRow]) -> AppConfigAllowListData:
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise AppConfigAllowListNotFound(
                    f"App config allow-list entry {updater.pk_value} not found"
                )
            return result.row.to_data()

    @app_config_allow_list_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigAllowListRow]) -> AppConfigAllowListData:
        async with self._ops.write_ops() as w:
            result = await w.purge(purger)
            if result is None:
                raise AppConfigAllowListNotFound("App config allow-list entry not found")
            return result.row.to_data()

    @app_config_allow_list_db_source_resilience.apply()
    async def search(self, querier: BatchQuerier) -> AppConfigAllowListSearchResult:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigAllowListRow), querier)
            items = [row.AppConfigAllowListRow.to_data() for row in result.rows]
            return AppConfigAllowListSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
