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
from ai.backend.manager.data.reservoir_registry.types import (
    ReservoirRegistryData,
    ReservoirRegistryListResult,
)
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
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
        self, reservoir_id: uuid.UUID
    ) -> ReservoirRegistryData:
        data = await self._db_source.get_reservoir_registry_data_by_id(reservoir_id)
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def get_registries_by_ids(
        self, reservoir_ids: list[uuid.UUID]
    ) -> list[ReservoirRegistryData]:
        results = await self._db_source.get_registries_by_ids(reservoir_ids)
        for data in results:
            await self._stateful_source.set_registry(data.to_stateful_data())
        return results

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        data = await self._db_source.get_registry_data_by_name(name)
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> ReservoirRegistryData:
        data = await self._db_source.get_registry_data_by_artifact_id(artifact_id)
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def create(
        self, creator: Creator[ReservoirRegistryRow], meta: ArtifactRegistryCreatorMeta
    ) -> ReservoirRegistryData:
        data = await self._db_source.create(creator, meta)
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def update(
        self,
        updater: Updater[ReservoirRegistryRow],
        meta: ArtifactRegistryModifierMeta,
    ) -> ReservoirRegistryData:
        data = await self._db_source.update(updater, meta)
        await self._stateful_source.set_registry(data.to_stateful_data())
        return data

    @reservoir_registry_repository_resilience.apply()
    async def delete(self, reservoir_id: uuid.UUID) -> uuid.UUID:
        result = await self._db_source.delete(reservoir_id)
        await self._stateful_source.delete_registry(reservoir_id)
        return result

    @reservoir_registry_repository_resilience.apply()
    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        results = await self._db_source.list_reservoir_registries()
        for data in results:
            await self._stateful_source.set_registry(data.to_stateful_data())
        return results

    @reservoir_registry_repository_resilience.apply()
    async def search_registries(
        self,
        querier: BatchQuerier,
    ) -> ReservoirRegistryListResult:
        return await self._db_source.search_registries(querier)
