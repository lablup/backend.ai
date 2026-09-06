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
from ai.backend.manager.data.reservoir_registry.types import (
    ReservoirRegistryData,
    ReservoirRegistryListResult,
)
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries.creators import ArtifactRegistryMetaCreator
from ai.backend.manager.models.artifact_registries.updaters import ArtifactRegistryMetaUpdater
from ai.backend.manager.models.reservoir_registry.creators import ReservoirRegistryCreator
from ai.backend.manager.models.reservoir_registry.purgers import ReservoirRegistryPurger
from ai.backend.manager.models.reservoir_registry.searchers import ReservoirRegistrySearcher
from ai.backend.manager.models.reservoir_registry.updaters import ReservoirRegistryUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.artifact_registry.provider import (
    ArtifactRegistryOpsProvider,
)
from ai.backend.manager.repositories.reservoir_registry.db_source.db_source import ReservoirDBSource

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
    _registry_ops: ArtifactRegistryOpsProvider

    def __init__(
        self, db: ExtendedAsyncSAEngine, registry_ops_provider: ArtifactRegistryOpsProvider
    ) -> None:
        self._db_source = ReservoirDBSource(db)
        self._registry_ops = registry_ops_provider

    @reservoir_registry_repository_resilience.apply()
    async def get_reservoir_registry_data_by_id(
        self, reservoir_id: uuid.UUID
    ) -> ReservoirRegistryData:
        return await self._db_source.get_reservoir_registry_data_by_id(reservoir_id)

    @reservoir_registry_repository_resilience.apply()
    async def get_registries_by_ids(
        self, reservoir_ids: list[uuid.UUID]
    ) -> list[ReservoirRegistryData]:
        return await self._db_source.get_registries_by_ids(reservoir_ids)

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        return await self._db_source.get_registry_data_by_name(name)

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> ReservoirRegistryData:
        return await self._db_source.get_registry_data_by_artifact_id(artifact_id)

    @reservoir_registry_repository_resilience.apply()
    async def create(
        self, creator: ReservoirRegistryCreator, meta: ArtifactRegistryCreatorMeta
    ) -> ReservoirRegistryData:
        """Register a Reservoir registry under the name given beside it."""
        async with self._registry_ops.write_ops() as w:
            return await w.create_registry(
                creator,
                ArtifactRegistryMetaCreator(name=meta.name, type=ArtifactRegistryType.RESERVOIR),
            )

    @reservoir_registry_repository_resilience.apply()
    async def update(
        self,
        updater: ReservoirRegistryUpdater,
        meta: ArtifactRegistryModifierMeta,
    ) -> ReservoirRegistryData:
        """Edit a Reservoir registry.

        Raises ArtifactRegistryNotFoundError if the registry does not exist.
        """
        async with self._registry_ops.write_ops() as w:
            data = await w.update_registry(
                updater,
                ArtifactRegistryMetaUpdater(registry_id=updater.registry_id, name=meta.name),
            )
            if data is None:
                raise ArtifactRegistryNotFoundError(
                    f"Reservoir registry with ID {updater.registry_id} not found"
                )
            return data

    @reservoir_registry_repository_resilience.apply()
    async def delete(self, reservoir_id: ArtifactRegistryID) -> uuid.UUID:
        """Remove a Reservoir registry, the row naming it, and the node it was.

        Raises ArtifactRegistryNotFoundError if the registry does not exist.
        """
        async with self._registry_ops.write_ops() as w:
            deleted_id = await w.purge_registry(ReservoirRegistryPurger(registry_id=reservoir_id))
            if deleted_id is None:
                raise ArtifactRegistryNotFoundError(
                    f"Reservoir registry with ID {reservoir_id} not found"
                )
            return deleted_id

    @reservoir_registry_repository_resilience.apply()
    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        return await self._db_source.list_reservoir_registries()

    @reservoir_registry_repository_resilience.apply()
    async def search_registries(
        self,
        searcher: ReservoirRegistrySearcher,
    ) -> ReservoirRegistryListResult:
        async with self._registry_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return ReservoirRegistryListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
