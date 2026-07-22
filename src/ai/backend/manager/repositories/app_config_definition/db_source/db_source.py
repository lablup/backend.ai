"""Database source for app config definition repository operations.

Each public method only executes the spec/wrapper handed in by the caller,
bound to a single session through the injected ``DBOpsProvider``.
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.app_config_definition.types import (
    AppConfigDefinitionData,
    AppConfigDefinitionListResult,
)
from ai.backend.manager.errors.app_config import AppConfigDefinitionNotFound
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.base import BatchQuerier, Creator, Purger, Querier
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigDefinitionDBSource",)

app_config_definition_db_source_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.DB_SOURCE, layer=LayerType.APP_CONFIG_DEFINITION_DB_SOURCE)
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


class AppConfigDefinitionDBSource:
    """Database source for app config definition operations."""

    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    @app_config_definition_db_source_resilience.apply()
    async def create(
        self,
        creator: Creator[AppConfigDefinitionRow],
    ) -> AppConfigDefinitionData:
        async with self._ops.write_ops() as w:
            created = await w.create(creator)
            return created.row.to_data()

    @app_config_definition_db_source_resilience.apply()
    async def get_by_id(self, definition_id: AppConfigDefinitionID) -> AppConfigDefinitionData:
        async with self._ops.read_ops() as r:
            result = await r.query(
                Querier(row_class=AppConfigDefinitionRow, pk_value=definition_id)
            )
            if result is None:
                raise AppConfigDefinitionNotFound(
                    f"App config definition {definition_id} not found"
                )
            return result.row.to_data()

    @app_config_definition_db_source_resilience.apply()
    async def purge(self, purger: Purger[AppConfigDefinitionRow]) -> AppConfigDefinitionData:
        async with self._ops.write_ops() as w:
            result = await w.purge(purger)
            if result is None:
                raise AppConfigDefinitionNotFound("App config definition not found")
            return result.row.to_data()

    @app_config_definition_db_source_resilience.apply()
    async def admin_search(self, querier: BatchQuerier) -> AppConfigDefinitionListResult:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigDefinitionRow), querier)
            items = [row.AppConfigDefinitionRow.to_data() for row in result.rows]
            return AppConfigDefinitionListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
