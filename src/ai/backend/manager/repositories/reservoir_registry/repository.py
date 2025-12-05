import uuid

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.reservoir_registry.creator import ReservoirRegistryCreator
from ai.backend.manager.data.reservoir_registry.modifier import ReservoirRegistryModifier
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.reservoir_registry.db_source.db_source import ReservoirDBSource
from ai.backend.manager.repositories.reservoir_registry.stateful_source.stateful_source import (
    ReservoirStatefulSource,
)

reservoir_registry_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.RESERVOIR_REGISTRY_REPOSITORY)
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


class ReservoirRegistryRepository:
    """Repository layer that delegates to data source."""

    _db_source: ReservoirDBSource
    _stateful_source: ReservoirStatefulSource

    def __init__(
        self, db: ExtendedAsyncSAEngine, valkey_artifact_registry: ValkeyArtifactRegistryClient
    ) -> None:
        self._db_source = ReservoirDBSource(db)
        self._stateful_source = ReservoirStatefulSource(valkey_artifact_registry)

    @reservoir_registry_repository_resilience.apply()
    async def get_reservoir_registry_data_by_id(
        self, registry_id: uuid.UUID
    ) -> ReservoirRegistryData:
        """Get reservoir registry data by artifact registry ID."""
        data = await self._db_source.get_reservoir_registry_data_by_id(registry_id)
        # Populate cache
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def get_registries_by_ids(
        self, registry_ids: list[uuid.UUID]
    ) -> list[ReservoirRegistryData]:
        """Get multiple reservoir registries by artifact registry IDs."""
        results = await self._db_source.get_registries_by_ids(registry_ids)
        # Populate cache for all retrieved registries
        for data in results:
            await self._stateful_source.set_registry(data.to_stateful_data())
        return results

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        """Get reservoir registry data by name."""
        data = await self._db_source.get_registry_data_by_name(name)
        # Populate cache
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> ReservoirRegistryData:
        """Get reservoir registry data by artifact ID."""
        data = await self._db_source.get_registry_data_by_artifact_id(artifact_id)
        # Populate cache
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def create(
        self, creator: ReservoirRegistryCreator, meta: ArtifactRegistryCreatorMeta
    ) -> ReservoirRegistryData:
        """Create a new reservoir registry."""
        # Write-through caching: DB insert then cache update
        data = await self._db_source.create(creator, meta)
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def update(
        self,
        registry_id: uuid.UUID,
        modifier: ReservoirRegistryModifier,
        meta: ArtifactRegistryModifierMeta,
    ) -> ReservoirRegistryData:
        """Update an existing reservoir registry by artifact registry ID."""
        # Write-through caching: DB update then cache update
        data = await self._db_source.update(registry_id, modifier, meta)
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def delete(self, registry_id: uuid.UUID) -> uuid.UUID:
        """Delete a reservoir registry by artifact registry ID."""
        # Delete from DB
        result = await self._db_source.delete(registry_id)
        # Invalidate cache
        await self._stateful_source.delete_registry(registry_id)
        return result

    @reservoir_registry_repository_resilience.apply()
    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        """List all reservoir registries."""
        results = await self._db_source.list_reservoir_registries()
        # Populate cache for all retrieved registries
        for data in results:
            await self._stateful_source.set_registry(data.to_stateful_data())
        return results
