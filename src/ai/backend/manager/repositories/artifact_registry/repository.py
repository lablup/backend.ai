import uuid

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryData,
    ArtifactRegistryListResult,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact_registry.db_source.db_source import (
    ArtifactRegistryDBSource,
)
from ai.backend.manager.repositories.base import BatchQuerier

artifact_registry_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.ARTIFACT_REGISTRY_REPOSITORY)
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


class ArtifactRegistryRepository:
    """Repository layer that delegates to data source."""

    _db_source: ArtifactRegistryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ArtifactRegistryDBSource(db)

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_data(self, registry_id: uuid.UUID) -> ArtifactRegistryData:
        return await self._db_source.get_artifact_registry_data(registry_id)

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_data_by_name(self, registry_name: str) -> ArtifactRegistryData:
        return await self._db_source.get_artifact_registry_data_by_name(registry_name)

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_datas(
        self, registry_ids: list[uuid.UUID]
    ) -> list[ArtifactRegistryData]:
        return await self._db_source.get_artifact_registry_datas(registry_ids)

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_type(self, registry_id: uuid.UUID) -> ArtifactRegistryType:
        return await self._db_source.get_artifact_registry_type(registry_id)

    @artifact_registry_repository_resilience.apply()
    async def list_artifact_registry_data(self) -> list[ArtifactRegistryData]:
        return await self._db_source.list_artifact_registry_data()

    @artifact_registry_repository_resilience.apply()
    async def search_artifact_registries(
        self,
        querier: BatchQuerier,
    ) -> ArtifactRegistryListResult:
        """Searches artifact registries with total count."""
        return await self._db_source.search_artifact_registries(querier=querier)
