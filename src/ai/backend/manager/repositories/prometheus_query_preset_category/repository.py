from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
    PrometheusQueryPresetCategoryListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator

from .db_source import PrometheusQueryPresetCategoryDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.prometheus_query_preset_category import (
        PrometheusQueryPresetCategoryRow,
    )
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("PrometheusQueryPresetCategoryRepository",)


prometheus_query_preset_category_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.PROMETHEUS_QUERY_PRESET_REPOSITORY,
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class PrometheusQueryPresetCategoryRepository:
    """Repository for prometheus query preset category data access."""

    _db_source: PrometheusQueryPresetCategoryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = PrometheusQueryPresetCategoryDBSource(db)

    @prometheus_query_preset_category_repository_resilience.apply()
    async def create(
        self,
        creator: Creator[PrometheusQueryPresetCategoryRow],
    ) -> PrometheusQueryPresetCategoryData:
        return await self._db_source.create(creator)

    @prometheus_query_preset_category_repository_resilience.apply()
    async def delete(self, category_id: UUID) -> bool:
        return await self._db_source.delete(category_id)

    @prometheus_query_preset_category_repository_resilience.apply()
    async def get_by_id(self, category_id: UUID) -> PrometheusQueryPresetCategoryData:
        return await self._db_source.get_by_id(category_id)

    @prometheus_query_preset_category_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> PrometheusQueryPresetCategoryListResult:
        """Searches prometheus query preset categories with total count."""
        return await self._db_source.search(querier=querier)
