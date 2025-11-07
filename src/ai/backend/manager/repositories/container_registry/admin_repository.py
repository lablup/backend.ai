from typing import Optional

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .db_source.db_source import ContainerRegistryDBSource

container_registry_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.CONTAINER_REGISTRY_REPOSITORY)
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


class AdminContainerRegistryRepository:
    _db_source: ContainerRegistryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ContainerRegistryDBSource(db)

    @container_registry_repository_resilience.apply()
    async def clear_images_force(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        """
        Forcefully clear images from a container registry without any validation.
        This is an admin-only operation that should be used with caution.
        """
        # Clear images
        await self._db_source.mark_images_as_deleted(registry_name, project)

        # Return registry data
        return await self._db_source.fetch_by_registry_and_project(registry_name, project)

    @container_registry_repository_resilience.apply()
    async def get_by_registry_and_project_force(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        """
        Forcefully get container registry by name and project without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._db_source.fetch_by_registry_and_project(registry_name, project)

    @container_registry_repository_resilience.apply()
    async def get_by_registry_name_force(self, registry_name: str) -> list[ContainerRegistryData]:
        """
        Forcefully get container registries by name without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._db_source.fetch_by_registry_name(registry_name)

    @container_registry_repository_resilience.apply()
    async def get_all_force(self) -> list[ContainerRegistryData]:
        """
        Forcefully get all container registries without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._db_source.fetch_all()
