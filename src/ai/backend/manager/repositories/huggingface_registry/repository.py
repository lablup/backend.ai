import uuid

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.data.artifact_registry.types import HuggingFaceRegistryData
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.huggingface_registry.creator import HuggingFaceRegistryCreator
from ai.backend.manager.data.huggingface_registry.modifier import HuggingFaceRegistryModifier
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.huggingface_registry.db_source.db_source import (
    HuggingFaceDBSource,
)
from ai.backend.manager.repositories.huggingface_registry.stateful_source.stateful_source import (
    HuggingFaceStatefulSource,
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
    _stateful_source: HuggingFaceStatefulSource

    def __init__(
        self, db: ExtendedAsyncSAEngine, valkey_artifact_registry: ValkeyArtifactRegistryClient
    ) -> None:
        self._db_source = HuggingFaceDBSource(db)
        self._stateful_source = HuggingFaceStatefulSource(valkey_artifact_registry)

    @huggingface_registry_repository_resilience.apply()
    async def get_registry_data_by_id(self, registry_id: uuid.UUID) -> HuggingFaceRegistryData:
        # Fetch from database (ID-based lookup cannot use name-based cache)
        data = await self._db_source.get_registry_data_by_id(registry_id)

        # Update cache using registry name for future name-based lookups
        await self._stateful_source.set_registry(data.name, data)

        return data

    @huggingface_registry_repository_resilience.apply()
    async def get_registry_data_by_name(self, name: str) -> HuggingFaceRegistryData:
        # Try to get from cache first (read-through pattern)
        cached_data = await self._stateful_source.get_registry(name)
        if cached_data is not None:
            return cached_data

        # Cache miss - fetch from database
        data = await self._db_source.get_registry_data_by_name(name)

        # Update cache for future requests
        await self._stateful_source.set_registry(name, data)

        return data

    @huggingface_registry_repository_resilience.apply()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> HuggingFaceRegistryData:
        # Fetch from database (artifact_id-based queries cannot use cache lookup)
        data = await self._db_source.get_registry_data_by_artifact_id(artifact_id)

        # Update cache using registry name for future name-based lookups
        await self._stateful_source.set_registry(data.name, data)

        return data

    @huggingface_registry_repository_resilience.apply()
    async def create(
        self, creator: HuggingFaceRegistryCreator, meta: ArtifactRegistryCreatorMeta
    ) -> HuggingFaceRegistryData:
        # Create in database (write-through pattern)
        data = await self._db_source.create(creator, meta)

        # Update cache immediately using registry name
        await self._stateful_source.set_registry(data.name, data)

        return data

    @huggingface_registry_repository_resilience.apply()
    async def update(
        self,
        registry_id: uuid.UUID,
        modifier: HuggingFaceRegistryModifier,
        meta: ArtifactRegistryModifierMeta,
    ) -> HuggingFaceRegistryData:
        # Update in database (write-through pattern)
        data = await self._db_source.update(registry_id, modifier, meta)

        # Update cache immediately using registry name
        await self._stateful_source.set_registry(data.name, data)

        return data

    @huggingface_registry_repository_resilience.apply()
    async def delete(self, registry_id: uuid.UUID) -> uuid.UUID:
        # Fetch registry data to get the name for cache invalidation
        data = await self._db_source.get_registry_data_by_id(registry_id)
        registry_name = data.name

        # Delete from database
        deleted_id = await self._db_source.delete(registry_id)

        # Invalidate cache using registry name
        await self._stateful_source.delete_registry(registry_name)

        return deleted_id

    @huggingface_registry_repository_resilience.apply()
    async def get_registries_by_ids(
        self, registry_ids: list[uuid.UUID]
    ) -> list[HuggingFaceRegistryData]:
        # Fetch from database (batch queries)
        registries = await self._db_source.get_registries_by_ids(registry_ids)

        # Update cache for each registry using registry name
        for registry in registries:
            await self._stateful_source.set_registry(registry.name, registry)

        return registries

    @huggingface_registry_repository_resilience.apply()
    async def list_registries(self) -> list[HuggingFaceRegistryData]:
        # Fetch all registries from database
        registries = await self._db_source.list_registries()

        # Update cache for each registry using registry name
        for registry in registries:
            await self._stateful_source.set_registry(registry.name, registry)

        return registries
