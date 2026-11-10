import uuid

from ai.backend.common.exception import (
    BackendAIError,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.object_storage.types import ObjectStorageData, ObjectStorageListResult
from ai.backend.manager.models.object_storage.searchers import ObjectStorageSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.object_storage.db_source.db_source import ObjectStorageDBSource
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

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

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops_provider: V2DBOpsProvider) -> None:
        self._db_source = ObjectStorageDBSource(db, v2_ops_provider)

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
    async def list_object_storages(self) -> list[ObjectStorageData]:
        return await self._db_source.list_object_storages()

    @object_storage_repository_resilience.apply()
    async def search(
        self,
        searcher: ObjectStorageSearcher,
    ) -> ObjectStorageListResult:
        return await self._db_source.search(searcher)
