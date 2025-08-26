import uuid

import sqlalchemy as sa

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.reservoir.creator import ReservoirCreator
from ai.backend.manager.data.reservoir.modifier import ReservoirModifier
from ai.backend.manager.data.reservoir.types import ReservoirData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.reservoir import ReservoirRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for reservoir repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT_REGISTRY)


class ReservoirRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_reservoir_data_by_id(self, reservoir_id: uuid.UUID) -> ReservoirData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ReservoirRow).where(ReservoirRow.id == reservoir_id)
            )
            row: ReservoirRow = result.scalar_one_or_none()
            if row is None:
                raise ValueError(f"Reservoir with ID {reservoir_id} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def get_reservoir_data_by_name(self, name: str) -> ReservoirData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(sa.select(ReservoirRow).where(ReservoirRow.name == name))
            row: ReservoirRow = result.scalar_one_or_none()
            if row is None:
                raise ValueError(f"Reservoir with name {name} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def create(self, creator: ReservoirCreator) -> ReservoirData:
        """
        Create a new Reservoir entry.
        """
        async with self._db.begin_session() as db_session:
            reservoir_data = creator.fields_to_store()
            reservoir_row = ReservoirRow(**reservoir_data)
            db_session.add(reservoir_row)
            await db_session.flush()
            await db_session.refresh(reservoir_row)
            return reservoir_row.to_dataclass()

    @repository_decorator()
    async def update(self, reservoir_id: uuid.UUID, modifier: ReservoirModifier) -> ReservoirData:
        """
        Update an existing Reservoir entry in the database.
        """
        async with self._db.begin_session() as db_session:
            data = modifier.fields_to_update()
            update_stmt = (
                sa.update(ReservoirRow)
                .where(ReservoirRow.id == reservoir_id)
                .values(**data)
                .returning(*sa.select(ReservoirRow).selected_columns)
            )
            stmt = sa.select(ReservoirRow).from_statement(update_stmt)
            row: ReservoirRow = (await db_session.execute(stmt)).scalars().one()
            return row.to_dataclass()

    @repository_decorator()
    async def delete(self, reservoir_id: uuid.UUID) -> uuid.UUID:
        """
        Delete an existing Reservoir entry from the database.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(ReservoirRow)
                .where(ReservoirRow.id == reservoir_id)
                .returning(ReservoirRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_id = result.scalar()
            return deleted_id

    @repository_decorator()
    async def list_reservoirs(self) -> list[ReservoirData]:
        """
        List all Reservoir entries from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ReservoirRow)
            result = await db_session.execute(query)
            rows: list[ReservoirRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
