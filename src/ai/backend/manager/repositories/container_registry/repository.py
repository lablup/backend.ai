import logging

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
    KnownContainerRegistry,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.db_source.db_source import (
    ContainerRegistryDBSource,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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

    def __init__(self, db_source: ContainerRegistryDBSource) -> None:
        self._db_source = db_source

    @container_registry_repository_resilience.apply()
    async def create_registry(
        self,
        creator: Creator[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        return await self._db_source.insert_registry(creator)

    @container_registry_repository_resilience.apply()
    async def modify_registry(
        self,
        updater: Updater[ContainerRegistryRow],
    ) -> ContainerRegistryData:
        return await self._db_source.update_registry(updater)

    @container_registry_repository_resilience.apply()
    async def delete_registry(self, purger: Purger[ContainerRegistryRow]) -> ContainerRegistryData:
        return await self._db_source.remove_registry(purger)

    @container_registry_repository_resilience.apply()
    async def get_by_registry_and_project(
        self,
        registry_name: str,
        project: str | None = None,
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
        project: str | None = None,
    ) -> ContainerRegistryData:
        return await self._db_source.clear_registry_images(registry_name, project)

    @container_registry_repository_resilience.apply()
    async def get_known_registries(self) -> list[KnownContainerRegistry]:
        return await self._db_source.fetch_known_registries()

    @container_registry_repository_resilience.apply()
    async def get_registry_row_for_scanner(
        self,
        registry_name: str,
        project: str | None = None,
    ) -> ContainerRegistryRow:
        """
        Get the raw ContainerRegistryRow object needed for container registry scanner.
        Raises ContainerRegistryNotFound if registry is not found.
        TODO: Refactor to return ContainerRegistryData when Registry Scanner is updated
        """
        return await self._db_source.fetch_registry_row_for_scanner(registry_name, project)
