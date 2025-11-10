from typing import Optional
from uuid import UUID

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryCreator,
    ContainerRegistryData,
    ContainerRegistryModifier,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.db_source.db_source import (
    ContainerRegistryDBSource,
)

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


class ContainerRegistryRepository:
    _db_source: ContainerRegistryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ContainerRegistryDBSource(db)

    @container_registry_repository_resilience.apply()
    async def create_registry(
        self,
        creator: ContainerRegistryCreator,
    ) -> ContainerRegistryData:
        return await self._db_source.insert_registry(creator)

    @container_registry_repository_resilience.apply()
    async def modify_registry(
        self,
        registry_id: UUID,
        modifier: ContainerRegistryModifier,
    ) -> ContainerRegistryData:
        return await self._db_source.update_registry(registry_id, modifier)

    @container_registry_repository_resilience.apply()
    async def delete_registry(
        self,
        registry_id: UUID,
    ) -> ContainerRegistryData:
        return await self._db_source.delete_registry(registry_id)

    @container_registry_repository_resilience.apply()
    async def get_by_registry_and_project(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        return await self._db_source.fetch_by_registry_and_project(registry_name, project)

    @container_registry_repository_resilience.apply()
    async def get_by_registry_name(self, registry_name: str) -> list[ContainerRegistryData]:
        return await self._db_source.fetch_by_registry_name(registry_name)

    @container_registry_repository_resilience.apply()
    async def get_all(self) -> list[ContainerRegistryData]:
        return await self._db_source.fetch_all()

    @container_registry_repository_resilience.apply()
    async def clear_images(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryData:
        # Clear images
        await self._db_source.mark_images_as_deleted(registry_name, project)

        # Return registry data
        return await self._db_source.fetch_by_registry_and_project(registry_name, project)

    @container_registry_repository_resilience.apply()
    async def get_known_registries(self) -> dict[str, str]:
        return await self._db_source.fetch_known_registries()

    @container_registry_repository_resilience.apply()
    async def get_registry_row_for_scanner(
        self,
        registry_name: str,
        project: Optional[str] = None,
    ) -> ContainerRegistryRow:
        """
        Get the raw ContainerRegistryRow object needed for container registry scanner.
        Raises ContainerRegistryNotFound if registry is not found.
        """
        return await self._db_source.fetch_registry_row(registry_name, project)
