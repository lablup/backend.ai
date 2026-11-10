import uuid

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.huggingface_registry.types import (
    HuggingFaceRegistryData,
    HuggingFaceRegistryListResult,
)
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.huggingface_registry.db_source.db_source import (
    HuggingFaceDBSource,
)

huggingface_registry_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY, layer=LayerType.HUGGINGFACE_REGISTRY_REPOSITORY
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


class HuggingFaceRepository:
    """Repository layer that delegates to data source."""

    _db_source: HuggingFaceDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = HuggingFaceDBSource(db)

    @huggingface_registry_repository_resilience.apply()
    async def get_registry_data_by_id(self, registry_id: uuid.UUID) -> HuggingFaceRegistryData:
        return await self._db_source.get_registry_data_by_id(registry_id)

    @huggingface_registry_repository_resilience.apply()
    async def get_registry_data_by_name(self, name: str) -> HuggingFaceRegistryData:
        return await self._db_source.get_registry_data_by_name(name)

    @huggingface_registry_repository_resilience.apply()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> HuggingFaceRegistryData:
        return await self._db_source.get_registry_data_by_artifact_id(artifact_id)

    @huggingface_registry_repository_resilience.apply()
    async def create(
        self, creator: Creator[HuggingFaceRegistryRow], meta: ArtifactRegistryCreatorMeta
    ) -> HuggingFaceRegistryData:
        return await self._db_source.create(creator, meta)

    @huggingface_registry_repository_resilience.apply()
    async def update(
        self,
        updater: Updater[HuggingFaceRegistryRow],
        meta: ArtifactRegistryModifierMeta,
    ) -> HuggingFaceRegistryData:
        return await self._db_source.update(updater, meta)

    @huggingface_registry_repository_resilience.apply()
    async def delete(self, registry_id: uuid.UUID) -> uuid.UUID:
        return await self._db_source.delete(registry_id)

    @huggingface_registry_repository_resilience.apply()
    async def get_registries_by_ids(
        self, registry_ids: list[uuid.UUID]
    ) -> list[HuggingFaceRegistryData]:
        return await self._db_source.get_registries_by_ids(registry_ids)

    @huggingface_registry_repository_resilience.apply()
    async def list_registries(self) -> list[HuggingFaceRegistryData]:
        return await self._db_source.list_registries()

    @huggingface_registry_repository_resilience.apply()
    async def search_registries(
        self,
        querier: BatchQuerier,
    ) -> HuggingFaceRegistryListResult:
        """Searches HuggingFace registries with total count."""
        return await self._db_source.search_registries(querier=querier)
