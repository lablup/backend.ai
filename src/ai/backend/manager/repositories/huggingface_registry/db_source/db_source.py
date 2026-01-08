from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.huggingface_registry.types import (
    HuggingFaceRegistryData,
    HuggingFaceRegistryListResult,
)
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater


class HuggingFaceDBSource:
    """Database source for HuggingFace registry operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_registry_data_by_id(self, registry_id: uuid.UUID) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == registry_id)
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            row: HuggingFaceRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return row.to_dataclass()

    async def get_registry_data_by_name(self, name: str) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.name == name)
                .options(
                    selectinload(ArtifactRegistryRow.huggingface_registries).selectinload(
                        HuggingFaceRegistryRow.meta
                    )
                )
            )
            row: ArtifactRegistryRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {name} not found")
            return row.huggingface_registries.to_dataclass()

    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> HuggingFaceRegistryData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .options(
                    selectinload(ArtifactRow.huggingface_registry).selectinload(
                        HuggingFaceRegistryRow.meta
                    ),
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            return row.huggingface_registry.to_dataclass()

    async def create(
        self, creator: Creator[HuggingFaceRegistryRow], meta: ArtifactRegistryCreatorMeta
    ) -> HuggingFaceRegistryData:
        """
        Create a new Hugging Face registry entry.
        """
        async with self._db.begin_session() as db:
            creator_result = await execute_creator(db, creator)
            new_row = creator_result.row

            reg_insert = sa.insert(ArtifactRegistryRow).values(
                name=meta.name,
                registry_id=new_row.id,
                type=ArtifactRegistryType.HUGGINGFACE,
            )
            await db.execute(reg_insert)

            stmt = (
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == new_row.id)
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            row: HuggingFaceRegistryRow | None = (await db.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {new_row.id} not found")

            return row.to_dataclass()

    async def update(
        self,
        updater: Updater[HuggingFaceRegistryRow],
        meta: ArtifactRegistryModifierMeta,
    ) -> HuggingFaceRegistryData:
        """
        Update an existing Hugging Face registry entry in the database.
        """
        async with self._db.begin_session() as db_session:
            result = await execute_updater(db_session, updater)
            if result is None:
                raise ArtifactRegistryNotFoundError(
                    f"HuggingFace registry with ID {updater.pk_value} not found"
                )
            updated_row_id = result.row.id

            if (name := meta.name.optional_value()) is not None:
                await db_session.execute(
                    sa.update(ArtifactRegistryRow)
                    .where(ArtifactRegistryRow.registry_id == updated_row_id)
                    .values(name=name)
                )

            # Reselect for the `selectinload`
            row = (
                await db_session.execute(
                    sa.select(HuggingFaceRegistryRow)
                    .where(HuggingFaceRegistryRow.id == updated_row_id)
                    .options(selectinload(HuggingFaceRegistryRow.meta))
                )
            ).scalar_one()

            return row.to_dataclass()

    async def delete(self, registry_id: uuid.UUID) -> uuid.UUID:
        """
        Delete an existing Hugging Face registry entry from the database.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == registry_id)
                .returning(HuggingFaceRegistryRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_id = result.scalar()

            delete_meta_query = sa.delete(ArtifactRegistryRow).where(
                ArtifactRegistryRow.id == registry_id
            )
            await db_session.execute(delete_meta_query)
            return deleted_id

    async def get_registries_by_ids(
        self, registry_ids: list[uuid.UUID]
    ) -> list[HuggingFaceRegistryData]:
        """
        Get multiple Hugging Face registry entries by their IDs in a single query.
        """
        async with self._db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id.in_(registry_ids))
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            rows: list[HuggingFaceRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def list_registries(self) -> list[HuggingFaceRegistryData]:
        """
        List all Hugging Face registry entries from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(HuggingFaceRegistryRow).options(
                selectinload(HuggingFaceRegistryRow.meta)
            )
            result = await db_session.execute(query)
            rows: list[HuggingFaceRegistryRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def search_registries(
        self,
        querier: BatchQuerier,
    ) -> HuggingFaceRegistryListResult:
        """Searches HuggingFace registries with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(HuggingFaceRegistryRow).options(
                selectinload(HuggingFaceRegistryRow.meta)
            )

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.HuggingFaceRegistryRow.to_dataclass() for row in result.rows]

            return HuggingFaceRegistryListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
