import uuid

import sqlalchemy as sa

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_data(self, registry_id: uuid.UUID) -> ArtifactRegistryData:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(ArtifactRegistryRow.registry_id == registry_id)
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return row.to_dataclass()

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_data_by_name(self, registry_name: str) -> ArtifactRegistryData:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(ArtifactRegistryRow.name == registry_name)
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {registry_name} not found")
            return row.to_dataclass()

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_datas(
        self, registry_ids: list[uuid.UUID]
    ) -> list[ArtifactRegistryData]:
        """
        Get multiple artifact registry entries by their IDs in a single query.
        """
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow).where(
                    ArtifactRegistryRow.registry_id.in_(registry_ids)
                )
            )
            rows: list[ArtifactRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @artifact_registry_repository_resilience.apply()
    async def get_artifact_registry_type(self, registry_id: uuid.UUID) -> ArtifactRegistryType:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(
                sa.select(ArtifactRegistryRow.type).where(
                    ArtifactRegistryRow.registry_id == registry_id
                )
            )
            typ = result.scalar_one_or_none()
            if typ is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return ArtifactRegistryType(typ)

    @artifact_registry_repository_resilience.apply()
    async def list_artifact_registry_data(self) -> list[ArtifactRegistryData]:
        async with self._db.begin_readonly_session() as session:
            result = await session.execute(sa.select(ArtifactRegistryRow))
            rows: list[ArtifactRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
