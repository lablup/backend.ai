import uuid

from ai.backend.common.exception import (
    BackendAIError,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.object_storage.types import ObjectStorageData, ObjectStorageListResult
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.object_storage.db_source.db_source import ObjectStorageDBSource

object_storage_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.OBJECT_STORAGE_REPOSITORY)
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


class ObjectStorageRepository:
    """Repository layer that delegates to data source."""

    _db_source: ObjectStorageDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ObjectStorageDBSource(db)

    @object_storage_repository_resilience.apply()
    async def get_by_name(self, storage_name: str) -> ObjectStorageData:
        return await self._db_source.get_by_name(storage_name)

    @object_storage_repository_resilience.apply()
    async def get_by_id(self, storage_id: uuid.UUID) -> ObjectStorageData:
        return await self._db_source.get_by_id(storage_id)

    @object_storage_repository_resilience.apply()
    async def get_by_namespace_id(self, storage_namespace_id: uuid.UUID) -> ObjectStorageData:
        return await self._db_source.get_by_namespace_id(storage_namespace_id)

    @object_storage_repository_resilience.apply()
    async def create(self, creator: Creator[ObjectStorageRow]) -> ObjectStorageData:
        return await self._db_source.create(creator)

    @object_storage_repository_resilience.apply()
    async def update(self, updater: Updater[ObjectStorageRow]) -> ObjectStorageData:
        return await self._db_source.update(updater)

    @object_storage_repository_resilience.apply()
    async def delete(self, storage_id: uuid.UUID) -> uuid.UUID:
        return await self._db_source.delete(storage_id)

    @object_storage_repository_resilience.apply()
    async def list_object_storages(self) -> list[ObjectStorageData]:
        return await self._db_source.list_object_storages()

    @object_storage_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> ObjectStorageListResult:
        return await self._db_source.search(querier)
