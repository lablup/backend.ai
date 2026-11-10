import uuid
<<<<<<< HEAD
=======
from collections.abc import Mapping, Sequence
>>>>>>> ca95a63b0 (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))

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
    ReservoirRegistryConnectionData,
    ReservoirRegistryData,
    ReservoirRegistryListResult,
)
<<<<<<< HEAD
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
=======
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries.creators import ArtifactRegistryMetaCreator
from ai.backend.manager.models.artifact_registries.updaters import ArtifactRegistryMetaUpdater
from ai.backend.manager.models.reservoir_registry.creators import ReservoirRegistryCreator
from ai.backend.manager.models.reservoir_registry.purgers import ReservoirRegistryPurger
from ai.backend.manager.models.reservoir_registry.queriers import BulkReservoirRegistryQuerier
from ai.backend.manager.models.reservoir_registry.searchers import ReservoirRegistrySearcher
from ai.backend.manager.models.reservoir_registry.updaters import ReservoirRegistryUpdater
from ai.backend.manager.models.specs.types import BulkResultWithFailures
>>>>>>> ca95a63b0 (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
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

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ReservoirDBSource(db)

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
    async def registry_connections(
        self, registry_ids: Sequence[ArtifactRegistryID]
    ) -> Mapping[EntityIdentifier, ReservoirRegistryConnectionData]:
        async with self._registry_ops.read_ops() as r:
            return await r.query_bulk_data(BulkReservoirRegistryQuerier(), registry_ids)

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
        self, creator: Creator[ReservoirRegistryRow], meta: ArtifactRegistryCreatorMeta
    ) -> ReservoirRegistryData:
        return await self._db_source.create(creator, meta)

    @reservoir_registry_repository_resilience.apply()
    async def update(
        self,
        updater: Updater[ReservoirRegistryRow],
        meta: ArtifactRegistryModifierMeta,
    ) -> ReservoirRegistryData:
        return await self._db_source.update(updater, meta)

    @reservoir_registry_repository_resilience.apply()
    async def delete(self, reservoir_id: uuid.UUID) -> uuid.UUID:
        return await self._db_source.delete(reservoir_id)

    @reservoir_registry_repository_resilience.apply()
    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        return await self._db_source.list_reservoir_registries()

    @reservoir_registry_repository_resilience.apply()
    async def search_registries(
        self,
        querier: BatchQuerier,
    ) -> ReservoirRegistryListResult:
        return await self._db_source.search_registries(querier)
