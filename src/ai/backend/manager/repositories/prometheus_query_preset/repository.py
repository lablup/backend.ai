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
from ai.backend.manager.data.prometheus_query_preset import (
    PrometheusQueryPresetData,
    PrometheusQueryPresetListResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator
from ai.backend.manager.repositories.base.updater import Updater

from .db_source import PrometheusQueryPresetDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.prometheus_query_preset import (
        PrometheusQueryPresetRow,
    )
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("PrometheusQueryPresetRepository",)


prometheus_query_preset_repository_resilience = Resilience(
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


class PrometheusQueryPresetRepository:
    """Repository for prometheus query preset data access."""

    _db_source: PrometheusQueryPresetDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = PrometheusQueryPresetDBSource(db)

    @prometheus_query_preset_repository_resilience.apply()
    async def create(
        self,
        creator: Creator[PrometheusQueryPresetRow],
    ) -> PrometheusQueryPresetData:
        """Creates a new prometheus query preset."""
        return await self._db_source.create(creator)

    @prometheus_query_preset_repository_resilience.apply()
    async def update(
        self,
        updater: Updater[PrometheusQueryPresetRow],
    ) -> PrometheusQueryPresetData:
        """Updates an existing prometheus query preset."""
        return await self._db_source.update(updater=updater)

    @prometheus_query_preset_repository_resilience.apply()
    async def delete(self, preset_id: UUID) -> bool:
        """Deletes a prometheus query preset."""
        return await self._db_source.delete(preset_id)

    @prometheus_query_preset_repository_resilience.apply()
    async def get_by_id(self, preset_id: UUID) -> PrometheusQueryPresetData:
        """Retrieves a prometheus query preset by ID."""
        return await self._db_source.get_by_id(preset_id)

    @prometheus_query_preset_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> PrometheusQueryPresetListResult:
        """Searches prometheus query presets with total count."""
        return await self._db_source.search(querier=querier)
