"""Repository for fetching container registry information for quota management."""

from __future__ import annotations

import abc

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.container_registry.types import PerProjectContainerRegistryInfo
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry_quota.db_source import (
    PerProjectRegistryQuotaDBSource,
)

per_project_registry_quota_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.CONTAINER_REGISTRY_REPOSITORY,
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


class AbstractPerProjectRegistryQuotaRepository(abc.ABC):
    @abc.abstractmethod
    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> PerProjectContainerRegistryInfo:
        raise NotImplementedError


class PerProjectRegistryQuotaRepository(AbstractPerProjectRegistryQuotaRepository):
    _db_source: PerProjectRegistryQuotaDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = PerProjectRegistryQuotaDBSource(db)

    @per_project_registry_quota_repository_resilience.apply()
    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> PerProjectContainerRegistryInfo:
        return await self._db_source.fetch_container_registry_row(scope_id)
