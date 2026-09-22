from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.service_catalog import ServiceCatalogID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.models.service_catalog.creators import ServiceCatalogEndpointCreator
from ai.backend.manager.models.service_catalog.purgers import ServiceCatalogEndpointBatchPurger
from ai.backend.manager.models.service_catalog.upserters import ServiceCatalogUpserter
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

__all__ = ("ServiceCatalogRepository",)

service_catalog_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SERVICE_CATALOG_REPOSITORY)
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


class ServiceCatalogRepository:
    _ops: V2DBOpsProvider

    def __init__(self, ops_provider: V2DBOpsProvider) -> None:
        self._ops = ops_provider

    @service_catalog_repository_resilience.apply()
    async def register(
        self,
        upserter: ServiceCatalogUpserter,
        endpoints: Sequence[ServiceCatalogEndpointCreator],
    ) -> ServiceCatalogID:
        """Upsert the service instance and replace its endpoints, in one transaction."""
        async with self._ops.write_ops() as w:
            service_id = await w.upsert_entity(upserter)
            await w.batch_purge_field_entities(service_id, ServiceCatalogEndpointBatchPurger())
            await w.atomic_create_field_entities(service_id, endpoints)
        return service_id
