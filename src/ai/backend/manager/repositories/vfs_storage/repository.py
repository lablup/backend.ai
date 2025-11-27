import uuid

from ai.backend.common.data.vfs_storage.types import VFSStorageData
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.vfs_storage.creator import VFSStorageCreator
from ai.backend.manager.data.vfs_storage.modifier import VFSStorageModifier
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
    async def create(self, creator: VFSStorageCreator) -> VFSStorageData:
        return await self._db_source.create(creator)

    @vfs_storage_repository_resilience.apply()
    async def update(self, storage_id: uuid.UUID, modifier: VFSStorageModifier) -> VFSStorageData:
        return await self._db_source.update(storage_id, modifier)

    @vfs_storage_repository_resilience.apply()
    async def delete(self, storage_id: uuid.UUID) -> uuid.UUID:
        return await self._db_source.delete(storage_id)

    @vfs_storage_repository_resilience.apply()
    async def list_vfs_storages(self) -> list[VFSStorageData]:
        return await self._db_source.list_vfs_storages()
