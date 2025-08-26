import uuid

import sqlalchemy as sa

from ai.backend.common.exception import ReservoirNotFoundError
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.reservoir.creator import ReservoirRegistryCreator
from ai.backend.manager.data.reservoir.modifier import ReservoirRegistryModifier
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.reservoir import ReservoirRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for reservoir repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT_REGISTRY)


class ReservoirRegistryRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_reservoir_registry_data_by_id(
        self, reservoir_id: uuid.UUID
    ) -> ReservoirRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ReservoirRegistryRow).where(ReservoirRegistryRow.id == reservoir_id)
            )
            row: ReservoirRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ReservoirNotFoundError(f"Reservoir with ID {reservoir_id} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def get_reservoir_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ReservoirRegistryRow).where(ReservoirRegistryRow.name == name)
            )
            row: ReservoirRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ReservoirNotFoundError(f"Reservoir with name {name} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def create(self, creator: ReservoirRegistryCreator) -> ReservoirRegistryData:
        """
        Create a new Reservoir entry.
        """
        async with self._db.begin_session() as db_session:
            reservoir_data = creator.fields_to_store()
            reservoir_row = ReservoirRegistryRow(**reservoir_data)
            db_session.add(reservoir_row)
            await db_session.flush()
            await db_session.refresh(reservoir_row)
            return reservoir_row.to_dataclass()

    @repository_decorator()
    async def update(
        self, reservoir_id: uuid.UUID, modifier: ReservoirRegistryModifier
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
                .returning(*sa.select(ReservoirRegistryRow).selected_columns)
            )
            stmt = sa.select(ReservoirRegistryRow).from_statement(update_stmt)
            row: ReservoirRegistryRow = (await db_session.execute(stmt)).scalars().one()
            return row.to_dataclass()

    @repository_decorator()
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
            return deleted_id

    @repository_decorator()
    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        """
        List all Reservoir entries from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ReservoirRegistryRow)
            result = await db_session.execute(query)
            rows: list[ReservoirRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
