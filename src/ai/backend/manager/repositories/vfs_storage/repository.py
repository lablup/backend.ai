import uuid

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.vfs_storage.types import VFSStorageData, VFSStorageListResult
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.vfs_storage.db_source.db_source import VFSStorageDBSource

vfs_storage_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.VFS_STORAGE_REPOSITORY)
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


class VFSStorageRepository:
    """Repository layer that delegates to data source."""

    _db_source: VFSStorageDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = VFSStorageDBSource(db)

    @vfs_storage_repository_resilience.apply()
    async def get_by_name(self, storage_name: str) -> VFSStorageData:
        return await self._db_source.get_by_name(storage_name)

    @vfs_storage_repository_resilience.apply()
    async def get_by_id(self, storage_id: uuid.UUID) -> VFSStorageData:
        return await self._db_source.get_by_id(storage_id)

    @vfs_storage_repository_resilience.apply()
    async def create(self, creator: Creator[VFSStorageRow]) -> VFSStorageData:
        return await self._db_source.create(creator)

    @vfs_storage_repository_resilience.apply()
    async def update(self, updater: Updater[VFSStorageRow]) -> VFSStorageData:
        return await self._db_source.update(updater)

    @vfs_storage_repository_resilience.apply()
    async def delete(self, storage_id: uuid.UUID) -> uuid.UUID:
        return await self._db_source.delete(storage_id)

    @vfs_storage_repository_resilience.apply()
    async def list_vfs_storages(self) -> list[VFSStorageData]:
        return await self._db_source.list_vfs_storages()

    @vfs_storage_repository_resilience.apply()
    async def search(
        self,
        querier: BatchQuerier,
    ) -> VFSStorageListResult:
        return await self._db_source.search(querier)
