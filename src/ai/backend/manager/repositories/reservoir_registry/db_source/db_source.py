import uuid
from collections.abc import Sequence
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.data.artifact.types import ArtifactRegistryType
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


class ReservoirDBSource:
    """Database source for reservoir registry operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_reservoir_registry_data_by_id(
        self, registry_id: uuid.UUID
    ) -> ReservoirRegistryData:
        """Get reservoir registry data by artifact registry ID."""
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.id == registry_id)
                .where(ArtifactRegistryRow.type == ArtifactRegistryType.RESERVOIR)
                .options(
                    selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                        ReservoirRegistryRow.meta
                    )
                )
            )
            row: Optional[ArtifactRegistryRow] = result.scalar_one_or_none()
            if row is None or row.reservoir_registries is None:
                raise ArtifactRegistryNotFoundError(
                    f"Reservoir registry with ID {registry_id} not found"
                )
            return row.reservoir_registries.to_dataclass()

    async def get_registries_by_ids(
        self, registry_ids: Sequence[uuid.UUID]
    ) -> list[ReservoirRegistryData]:
        """Get multiple Reservoir registry entries by their artifact registry IDs."""
        async with self._db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.id.in_(registry_ids))
                .where(ArtifactRegistryRow.type == ArtifactRegistryType.RESERVOIR)
                .options(
                    selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                        ReservoirRegistryRow.meta
                    )
                )
            )
            rows: Sequence[ArtifactRegistryRow] = result.scalars().all()
            return [
                row.reservoir_registries.to_dataclass()
                for row in rows
                if row.reservoir_registries is not None
            ]

    async def get_registry_data_by_name(self, name: str) -> ReservoirRegistryData:
        """Get reservoir registry data by name."""
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.name == name)
                .where(ArtifactRegistryRow.type == ArtifactRegistryType.RESERVOIR)
                .options(
                    selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                        ReservoirRegistryRow.meta
                    )
                )
            )
            row: Optional[ArtifactRegistryRow] = result.scalar_one_or_none()
            if row is None or row.reservoir_registries is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {name} not found")
            return row.reservoir_registries.to_dataclass()

    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> ReservoirRegistryData:
        """Get reservoir registry data by artifact ID."""
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
            row: Optional[ArtifactRow] = result.scalar_one_or_none()
            if row is None or row.reservoir_registry is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            return row.reservoir_registry.to_dataclass()

    async def create(
        self, creator: ReservoirRegistryCreator, meta: ArtifactRegistryCreatorMeta
    ) -> ReservoirRegistryData:
        """Create a new Reservoir entry."""
        async with self._db.begin_session() as db:
            reservoir_insert = (
                sa.insert(ReservoirRegistryRow)
                .values(**creator.fields_to_store())
                .returning(ReservoirRegistryRow.id)
            )
            reservoir_id = (await db.execute(reservoir_insert)).scalar_one()

            reg_insert = (
                sa.insert(ArtifactRegistryRow)
                .values(
                    name=meta.name,
                    registry_id=reservoir_id,
                    type=ArtifactRegistryType.RESERVOIR,
                )
                .returning(ArtifactRegistryRow.id)
            )
            artifact_registry_id = (await db.execute(reg_insert)).scalar_one()

            stmt = (
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.id == artifact_registry_id)
                .options(
                    selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                        ReservoirRegistryRow.meta
                    )
                )
            )

            row: Optional[ArtifactRegistryRow] = (await db.execute(stmt)).scalar_one_or_none()
            if row is None or row.reservoir_registries is None:
                raise ArtifactRegistryNotFoundError(
                    f"Registry with ID {artifact_registry_id} not found"
                )

            return row.reservoir_registries.to_dataclass()

    async def update(
        self,
        registry_id: uuid.UUID,
        modifier: ReservoirRegistryModifier,
        meta: ArtifactRegistryModifierMeta,
    ) -> ReservoirRegistryData:
        """Update an existing Reservoir entry by artifact registry ID."""
        async with self._db.begin_session() as db_session:
            # First get the reservoir_id from registry_id
            artifact_row = (
                await db_session.execute(
                    sa.select(ArtifactRegistryRow)
                    .where(ArtifactRegistryRow.id == registry_id)
                    .where(ArtifactRegistryRow.type == ArtifactRegistryType.RESERVOIR)
                )
            ).scalar_one_or_none()

            if artifact_row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")

            reservoir_id = artifact_row.registry_id
            data = modifier.fields_to_update()

            update_stmt = (
                sa.update(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id == reservoir_id)
                .values(**data)
                .returning(ReservoirRegistryRow.id)
            )
            result = await db_session.execute(update_stmt)
            updated_reservoir_id = result.scalar()

            if (name := meta.name.optional_value()) is not None:
                await db_session.execute(
                    sa.update(ArtifactRegistryRow)
                    .where(ArtifactRegistryRow.id == registry_id)
                    .values(name=name)
                )

            # Reselect for the `selectinload`
            row = (
                await db_session.execute(
                    sa.select(ArtifactRegistryRow)
                    .where(ArtifactRegistryRow.id == registry_id)
                    .options(
                        selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                            ReservoirRegistryRow.meta
                        )
                    )
                )
            ).scalar_one()

            return row.reservoir_registries.to_dataclass()

    async def delete(self, registry_id: uuid.UUID) -> uuid.UUID:
        """Delete an existing Reservoir entry by artifact registry ID."""
        async with self._db.begin_session() as db_session:
            # First get the reservoir_id from registry_id
            artifact_row = (
                await db_session.execute(
                    sa.select(ArtifactRegistryRow)
                    .where(ArtifactRegistryRow.id == registry_id)
                    .where(ArtifactRegistryRow.type == ArtifactRegistryType.RESERVOIR)
                )
            ).scalar_one_or_none()

            if artifact_row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")

            reservoir_id = artifact_row.registry_id

            delete_query = (
                sa.delete(ReservoirRegistryRow)
                .where(ReservoirRegistryRow.id == reservoir_id)
                .returning(ReservoirRegistryRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_reservoir_id = result.scalar()

            delete_meta_query = sa.delete(ArtifactRegistryRow).where(
                ArtifactRegistryRow.id == registry_id
            )
            await db_session.execute(delete_meta_query)
            return registry_id

    async def list_reservoir_registries(self) -> list[ReservoirRegistryData]:
        """List all Reservoir entries from the database."""
        async with self._db.begin_session() as db_session:
            query = (
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.type == ArtifactRegistryType.RESERVOIR)
                .options(
                    selectinload(ArtifactRegistryRow.reservoir_registries).selectinload(
                        ReservoirRegistryRow.meta
                    )
                )
            )
            result = await db_session.execute(query)
            rows: Sequence[ArtifactRegistryRow] = result.scalars().all()
            return [
                row.reservoir_registries.to_dataclass()
                for row in rows
                if row.reservoir_registries is not None
            ]
