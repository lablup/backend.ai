from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.common.exception import (
    BackendAIError,
    FailedToGetMetric,
    PrometheusQueryEvaluationFailed,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.data.prometheus_query_preset import (
    PrometheusQueryPresetData,
)
from ai.backend.manager.repositories.base.updater import Updater

from .db_source import PrometheusQueryPresetDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
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
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class PrometheusQueryPresetRepository:
    """Repository for prometheus query preset data access."""

    _db_source: PrometheusQueryPresetDBSource
    _prometheus_client: PrometheusClient

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        prometheus_client: PrometheusClient,
    ) -> None:
        self._db_source = PrometheusQueryPresetDBSource(db)
        self._prometheus_client = prometheus_client

    @prometheus_query_preset_repository_resilience.apply()
    async def update(
        self,
        updater: Updater[PrometheusQueryPresetRow],
    ) -> PrometheusQueryPresetData:
        """Updates an existing prometheus query preset."""
        return await self._db_source.update(updater=updater)

    @prometheus_query_preset_repository_resilience.apply()
    async def get_by_id(self, preset_id: UUID) -> PrometheusQueryPresetData:
        """Retrieves a prometheus query preset by ID."""
        return await self._db_source.get_by_id(preset_id)

    @prometheus_query_preset_repository_resilience.apply()
    async def preview_template(
        self,
        query_template: str,
        default_window: str,
    ) -> PrometheusResponse:
        """Render the template with empty matchers and run an instant query."""
        try:
            return await self._prometheus_client.preview_query_template(
                query_template=query_template,
                default_window=default_window,
            )
        except FailedToGetMetric as e:
            raise PrometheusQueryEvaluationFailed(str(e)) from e
