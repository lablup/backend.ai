from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class HuggingFaceDBSource:
    """Database source for HuggingFace registry operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_registry_data_by_id(self, registry_id: uuid.UUID) -> HuggingFaceRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id == registry_id)
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return row.to_dataclass()

    async def get_registry_data_by_name(self, name: str) -> HuggingFaceRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRegistryRow)
                .where(ArtifactRegistryRow.name == name)
                .options(
                    selectinload(ArtifactRegistryRow.huggingface_registries).selectinload(
                        HuggingFaceRegistryRow.meta
                    )
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with name {name} not found")
            if row.huggingface_registries is None:
                raise ArtifactRegistryNotFoundError(
                    f"HuggingFace registry not found for registry {name}"
                )
            return row.huggingface_registries.to_dataclass()

    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> HuggingFaceRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .options(
                    selectinload(ArtifactRow.huggingface_registry).selectinload(
                        HuggingFaceRegistryRow.meta
                    ),
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            if row.huggingface_registry is None:
                raise ArtifactRegistryNotFoundError(
                    f"HuggingFace registry not found for artifact {artifact_id}"
                )
            return row.huggingface_registry.to_dataclass()

    async def get_registries_by_ids(
        self, registry_ids: list[uuid.UUID]
    ) -> list[HuggingFaceRegistryData]:
        """
        Get multiple Hugging Face registry entries by their IDs in a single query.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.execute(
                sa.select(HuggingFaceRegistryRow)
                .where(HuggingFaceRegistryRow.id.in_(registry_ids))
                .options(selectinload(HuggingFaceRegistryRow.meta))
            )
            rows = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def list_registries(self) -> list[HuggingFaceRegistryData]:
        """
        List all Hugging Face registry entries from the database.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            query = sa.select(HuggingFaceRegistryRow).options(
                selectinload(HuggingFaceRegistryRow.meta)
            )
            result = await db_session.execute(query)
            rows = result.scalars().all()
            return [row.to_dataclass() for row in rows]
