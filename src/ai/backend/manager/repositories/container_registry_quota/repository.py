"""Repository for fetching container registry information for quota management."""

from __future__ import annotations

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.container_registry.types import PerProjectContainerRegistryInfo
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.repositories.container_registry.db_source import ContainerRegistryDBSource

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


# NOTE: Only one implementation exists for now, so no ABC is used.
# Introduce an abstract base class when multiple implementations are needed.
class PerProjectRegistryQuotaRepository:
    _db_source: ContainerRegistryDBSource

    def __init__(self, registry_db_source: ContainerRegistryDBSource) -> None:
        self._db_source = registry_db_source

    @per_project_registry_quota_repository_resilience.apply()
    async def fetch_container_registry_row(
        self, scope_id: ProjectScope
    ) -> PerProjectContainerRegistryInfo:
        registry = await self._db_source.fetch_image_commit_registry(scope_id.project_id)

        return PerProjectContainerRegistryInfo(
            id=registry.id,
            url=registry.url,
            registry_name=registry.registry_name,
            type=registry.type,
            project=registry.project or "",
            username=registry.username or "",
            password=registry.password or "",
            ssl_verify=registry.ssl_verify if registry.ssl_verify is not None else True,
            is_global=registry.is_global if registry.is_global is not None else False,
            extra=registry.extra or {},
        )
