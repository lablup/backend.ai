import uuid

from ai.backend.common.exception import (
    BackendAIError,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.storage_namespace.types import (
    StorageNamespaceData,
    StorageNamespaceListResult,
)
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.storage_namespace.db_source.db_source import (
    StorageNamespaceDBSource,
)

storage_namespace_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.STORAGE_NAMESPACE_REPOSITORY)
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


class StorageNamespaceRepository:
    """Repository layer that delegates to data source."""

    _db_source: StorageNamespaceDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = StorageNamespaceDBSource(db)

    @storage_namespace_repository_resilience.apply()
    async def get_by_storage_and_namespace(
        self, storage_id: uuid.UUID, namespace: str
    ) -> StorageNamespaceData:
        return await self._db_source.get_by_storage_and_namespace(storage_id, namespace)

    @storage_namespace_repository_resilience.apply()
    async def get_by_id(self, storage_namespace_id: uuid.UUID) -> StorageNamespaceData:
        return await self._db_source.get_by_id(storage_namespace_id)

    @storage_namespace_repository_resilience.apply()
    async def register(self, creator: Creator[StorageNamespaceRow]) -> StorageNamespaceData:
        return await self._db_source.register(creator)

    @storage_namespace_repository_resilience.apply()
    async def unregister(self, storage_id: uuid.UUID, namespace: str) -> uuid.UUID:
        return await self._db_source.unregister(storage_id, namespace)

    @storage_namespace_repository_resilience.apply()
    async def get_namespaces(self, storage_id: uuid.UUID) -> list[StorageNamespaceData]:
        return await self._db_source.get_namespaces(storage_id)

    @storage_namespace_repository_resilience.apply()
    async def get_all_namespaces_by_storage(self) -> dict[uuid.UUID, list[str]]:
        return await self._db_source.get_all_namespaces_by_storage()

    @storage_namespace_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> StorageNamespaceListResult:
        return await self._db_source.search(querier)
