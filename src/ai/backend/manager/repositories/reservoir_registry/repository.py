import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.data.artifact.types import ArtifactRegistryType
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
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

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
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @reservoir_registry_repository_resilience.apply()
    async def get_reservoir_registry_data_by_id(
        self, reservoir_id: uuid.UUID
    ) -> ReservoirRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id == reservoir_id)
                .options(selectinload(ReservoirRegistryRow.meta))
            )
            row: ReservoirRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Reservoir with ID {reservoir_id} not found")
            return row.to_dataclass()

    @reservoir_registry_repository_resilience.apply()
    async def get_registries_by_ids(
        self, reservoir_ids: list[uuid.UUID]
    ) -> list[ReservoirRegistryData]:
        """
        Get multiple Reservoir registry entries by their IDs in a single query.
        """
        async with self._db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id.in_(reservoir_ids))
                .options(selectinload(ReservoirRegistryRow.meta))
            )
            rows: list[ReservoirRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.name == name)
                .options(
                    selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                        ReservoirRegistryRow.meta
                    )
                )
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {name} not found")
            return row.reservoir_registries.to_dataclass()

    @reservoir_registry_repository_resilience.apply()
    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> ReservoirRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .options(
                    selectinload(ArtifactRow.reservoir_registry).selectinload(
                        ReservoirRegistryRow.meta
                    ),
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            return row.reservoir_registry.to_dataclass()

    @reservoir_registry_repository_resilience.apply()
    async def create(
        self, creator: ReservoirRegistryCreator, meta: ArtifactRegistryCreatorMeta
    ) -> ReservoirRegistryData:
        """
        Create a new Reservoir entry.
        """
        async with self._db.begin_session() as db:
            reservoir_insert = (
                sa.insert(ReservoirRegistryRow)
                .values(**creator.fields_to_store())
                .returning(ReservoirRegistryRow.id)
            )
            reservoir_id = (await db.execute(reservoir_insert)).scalar_one()

            reg_insert = sa.insert(ArtifactRegistryRow).values(
                name=meta.name,
                registry_id=reservoir_id,
                type=ArtifactRegistryType.RESERVOIR,
            )
            await db.execute(reg_insert)

            stmt = (
                sa.select(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id == reservoir_id)
                .options(selectinload(ReservoirRegistryRow.meta))
            )

            row: ReservoirRegistryRow | None = (await db.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {reservoir_id} not found")

            return row.to_dataclass()

    @reservoir_registry_repository_resilience.apply()
    async def update(
        self,
        reservoir_id: uuid.UUID,
        modifier: ReservoirRegistryModifier,
        meta: ArtifactRegistryModifierMeta,
    ) -> ReservoirRegistryData:
        """
        Update an existing Reservoir entry in the database.
        """
        async with self._db.begin_session() as db_session:
            data = modifier.fields_to_update()

            update_stmt = (
                sa.update(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id == reservoir_id)
                .values(**data)
                .returning(ReservoirRegistryRow.id)
            )
            result = await db_session.execute(update_stmt)
            inserted_row_id = result.scalar()

            if (name := meta.name.optional_value()) is not None:
                await db_session.execute(
                    sa.update(ArtifactRegistryRow)
                    .where(ArtifactRegistryRow.registry_id == inserted_row_id)
                    .values(name=name)
                )

            # Reselect for the `selectinload`
            row = (
                await db_session.execute(
                    sa.select(ReservoirRegistryRow)
                    .where(ReservoirRegistryRow.id == inserted_row_id)
                    .options(selectinload(ReservoirRegistryRow.meta))
                )
            ).scalar_one()

            return row.to_dataclass()

    @reservoir_registry_repository_resilience.apply()
    async def delete(self, reservoir_id: uuid.UUID) -> uuid.UUID:
        """
        Delete an existing Reservoir entry from the database.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id == reservoir_id)
                .returning(ReservoirRegistryRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_id = result.scalar()

            delete_meta_query = sa.delete(ArtifactRegistryRow).where(
                ArtifactRegistryRow.registry_id == reservoir_id
            )
            await db_session.execute(delete_meta_query)
            return deleted_id

    @reservoir_registry_repository_resilience.apply()
    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        """
        List all Reservoir entries from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ReservoirRegistryRow).options(selectinload(ReservoirRegistryRow.meta))
            result = await db_session.execute(query)
            rows: list[ReservoirRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
