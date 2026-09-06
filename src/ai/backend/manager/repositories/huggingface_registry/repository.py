import uuid

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
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
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries.creators import ArtifactRegistryMetaCreator
from ai.backend.manager.models.artifact_registries.updaters import ArtifactRegistryMetaUpdater
from ai.backend.manager.models.huggingface_registry.creators import HuggingFaceRegistryCreator
from ai.backend.manager.models.huggingface_registry.purgers import HuggingFaceRegistryPurger
from ai.backend.manager.models.huggingface_registry.searchers import HuggingFaceRegistrySearcher
from ai.backend.manager.models.huggingface_registry.updaters import HuggingFaceRegistryUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.huggingface_registry.db_source.db_source import (
    HuggingFaceDBSource,
)
from ai.backend.manager.repositories.ops.v2.artifact_registry.provider import (
    ArtifactRegistryOpsProvider,
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
    _registry_ops: ArtifactRegistryOpsProvider

    def __init__(
        self, db: ExtendedAsyncSAEngine, registry_ops_provider: ArtifactRegistryOpsProvider
    ) -> None:
        self._db_source = HuggingFaceDBSource(db)
        self._registry_ops = registry_ops_provider

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
        self, creator: HuggingFaceRegistryCreator, meta: ArtifactRegistryCreatorMeta
    ) -> HuggingFaceRegistryData:
        """Register a HuggingFace registry under the name given beside it."""
        async with self._registry_ops.write_ops() as w:
            return await w.create_registry(
                creator,
                ArtifactRegistryMetaCreator(name=meta.name, type=ArtifactRegistryType.HUGGINGFACE),
            )

    @huggingface_registry_repository_resilience.apply()
    async def update(
        self,
        updater: HuggingFaceRegistryUpdater,
        meta: ArtifactRegistryModifierMeta,
    ) -> HuggingFaceRegistryData:
        """Edit a HuggingFace registry.

        Raises ArtifactRegistryNotFoundError if the registry does not exist.
        """
        async with self._registry_ops.write_ops() as w:
            data = await w.update_registry(
                updater,
                ArtifactRegistryMetaUpdater(registry_id=updater.registry_id, name=meta.name),
            )
            if data is None:
                raise ArtifactRegistryNotFoundError(
                    f"HuggingFace registry with ID {updater.registry_id} not found"
                )
            return data

    @huggingface_registry_repository_resilience.apply()
    async def delete(self, registry_id: ArtifactRegistryID) -> uuid.UUID:
        """Remove a HuggingFace registry, the row naming it, and the node it was.

        Raises ArtifactRegistryNotFoundError if the registry does not exist.
        """
        async with self._registry_ops.write_ops() as w:
            deleted_id = await w.purge_registry(HuggingFaceRegistryPurger(registry_id=registry_id))
            if deleted_id is None:
                raise ArtifactRegistryNotFoundError(
                    f"HuggingFace registry with ID {registry_id} not found"
                )
            return deleted_id

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
        searcher: HuggingFaceRegistrySearcher,
    ) -> HuggingFaceRegistryListResult:
        """Searches HuggingFace registries with total count."""
        async with self._registry_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return HuggingFaceRegistryListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
