from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import with_expression

from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow
from ai.backend.manager.models.reservoir_registry.searchable_fields import (
    ReservoirRegistrySearchableFields,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ReservoirDBSource:
    """Database source for reservoir registry operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @staticmethod
    def _select_with_name() -> sa.sql.Select[Any]:
        """The registry row with the artifact_registries row's name on registry_name."""
        return (
            sa.select(ReservoirRegistryRow)
            .join(
                ArtifactRegistryRow,
                ArtifactRegistryRow.registry_id == ReservoirRegistryRow.id,
            )
            .options(with_expression(ReservoirRegistryRow.registry_name, ArtifactRegistryRow.name))
        )

    async def get_reservoir_registry_data_by_id(
        self, reservoir_id: uuid.UUID
    ) -> ReservoirRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.scalar(
                self._select_with_name().where(ReservoirRegistryRow.id == reservoir_id)
            )
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Reservoir with ID {reservoir_id} not found")
            return ReservoirRegistrySearchableFields.own.to_data(row)

    async def get_registries_by_ids(
        self, reservoir_ids: list[uuid.UUID]
    ) -> list[ReservoirRegistryData]:
        """
        Get multiple Reservoir registry entries by their IDs in a single query.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.execute(
                self._select_with_name().where(ReservoirRegistryRow.id.in_(reservoir_ids))
            )
            return [
                ReservoirRegistrySearchableFields.own.to_data(row) for row in result.scalars().all()
            ]

    async def get_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.scalar(
                self._select_with_name().where(ArtifactRegistryRow.name == name)
            )
            if row is None:
                raise ArtifactRegistryNotFoundError(
                    f"Reservoir registry not found for registry {name}"
                )
            return ReservoirRegistrySearchableFields.own.to_data(row)

    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> ReservoirRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            registry_id = await db_sess.scalar(
                sa.select(ArtifactRow.registry_id).where(ArtifactRow.id == artifact_id)
            )
            if registry_id is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            row = await db_sess.scalar(
                self._select_with_name().where(ReservoirRegistryRow.id == registry_id)
            )
            if row is None:
                raise ArtifactRegistryNotFoundError(
                    f"Reservoir registry not found for artifact {artifact_id}"
                )
            return ReservoirRegistrySearchableFields.own.to_data(row)

    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        """
        List all Reservoir entries from the database.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.execute(self._select_with_name())
            return [
                ReservoirRegistrySearchableFields.own.to_data(row) for row in result.scalars().all()
            ]
