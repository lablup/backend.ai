from typing import Optional

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .repository import ContainerRegistryRepository

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
    _repository: ContainerRegistryRepository

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._repository = ContainerRegistryRepository(db)

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
        return await self._repository.clear_images(registry_name, project)

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
        return await self._repository.get_by_registry_and_project(registry_name, project)

    @container_registry_repository_resilience.apply()
    async def get_by_registry_name_force(self, registry_name: str) -> list[ContainerRegistryData]:
        """
        Forcefully get container registries by name without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._repository.get_by_registry_name(registry_name)

    @container_registry_repository_resilience.apply()
    async def get_all_force(self) -> list[ContainerRegistryData]:
        """
        Forcefully get all container registries without any validation.
        This is an admin-only operation that should be used with caution.
        """
        return await self._repository.get_all()
