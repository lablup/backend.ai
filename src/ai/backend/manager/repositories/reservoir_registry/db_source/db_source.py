from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ReservoirDBSource:
    """Database source for reservoir registry operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_reservoir_registry_data_by_id(
        self, reservoir_id: uuid.UUID
    ) -> ReservoirRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id == reservoir_id)
                .options(selectinload(ReservoirRegistryRow.meta))
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Reservoir with ID {reservoir_id} not found")
            return row.to_dataclass()

    async def get_registries_by_ids(
        self, reservoir_ids: list[uuid.UUID]
    ) -> list[ReservoirRegistryData]:
        """
        Get multiple Reservoir registry entries by their IDs in a single query.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.execute(
                sa.select(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id.in_(reservoir_ids))
                .options(selectinload(ReservoirRegistryRow.meta))
            )
            rows = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def get_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.name == name)
                .options(
                    selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                        ReservoirRegistryRow.meta
                    )
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {name} not found")
            if row.reservoir_registries is None:
                raise ArtifactRegistryNotFoundError(
                    f"Reservoir registry not found for registry {name}"
                )
            return row.reservoir_registries.to_dataclass()

    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> ReservoirRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .options(
                    selectinload(ArtifactRow.reservoir_registry).selectinload(
                        ReservoirRegistryRow.meta
                    ),
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            if row.reservoir_registry is None:
                raise ArtifactRegistryNotFoundError(
                    f"Reservoir registry not found for artifact {artifact_id}"
                )
            return row.reservoir_registry.to_dataclass()

    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        """
        List all Reservoir entries from the database.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            query = sa.select(ReservoirRegistryRow).options(selectinload(ReservoirRegistryRow.meta))
            result = await db_session.execute(query)
            rows = result.scalars().all()
            return [row.to_dataclass() for row in rows]
