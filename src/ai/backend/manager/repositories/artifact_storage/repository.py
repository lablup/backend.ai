from __future__ import annotations

import uuid

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.artifact_storages.types import ArtifactStorageData
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact_storage.db_source.db_source import (
    ArtifactStorageDBSource,
)
from ai.backend.manager.repositories.base.updater import Updater

artifact_storage_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY,
                layer=LayerType.ARTIFACT_STORAGE_REPOSITORY,
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


class ArtifactStorageRepository:
    """Repository layer for artifact storage operations."""

    _db_source: ArtifactStorageDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ArtifactStorageDBSource(db)

    @artifact_storage_repository_resilience.apply()
    async def get_by_id(self, storage_id: uuid.UUID) -> ArtifactStorageData:
        return await self._db_source.get_by_id(storage_id)

    @artifact_storage_repository_resilience.apply()
    async def get_by_storage_id(self, storage_id: uuid.UUID) -> ArtifactStorageData:
        return await self._db_source.get_by_storage_id(storage_id)

    @artifact_storage_repository_resilience.apply()
    async def update(
        self,
        updater: Updater[ArtifactStorageRow],
    ) -> ArtifactStorageData:
        return await self._db_source.update(updater)
