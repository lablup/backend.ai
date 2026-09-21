from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import with_expression

from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.models.huggingface_registry.searchable_fields import (
    HuggingFaceRegistrySearchableFields,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class HuggingFaceDBSource:
    """Database source for HuggingFace registry operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @staticmethod
    def _select_with_name() -> sa.sql.Select[Any]:
        """The registry row with the artifact_registries row's name on registry_name."""
        return (
            sa.select(HuggingFaceRegistryRow)
            .join(
                ArtifactRegistryRow,
                ArtifactRegistryRow.registry_id == HuggingFaceRegistryRow.id,
            )
            .options(
                with_expression(HuggingFaceRegistryRow.registry_name, ArtifactRegistryRow.name)
            )
        )

    async def get_registry_data_by_id(self, registry_id: uuid.UUID) -> HuggingFaceRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.scalar(
                self._select_with_name().where(HuggingFaceRegistryRow.id == registry_id)
            )
            if row is None:
                raise ArtifactRegistryNotFoundError(f"Registry with ID {registry_id} not found")
            return HuggingFaceRegistrySearchableFields.own.to_data(row)

    async def get_registry_data_by_name(self, name: str) -> HuggingFaceRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.scalar(
                self._select_with_name().where(ArtifactRegistryRow.name == name)
            )
            if row is None:
                raise ArtifactRegistryNotFoundError(
                    f"HuggingFace registry not found for registry {name}"
                )
            return HuggingFaceRegistrySearchableFields.own.to_data(row)

    async def get_registry_data_by_artifact_id(
        self, artifact_id: uuid.UUID
    ) -> HuggingFaceRegistryData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            registry_id = await db_sess.scalar(
                sa.select(ArtifactRow.registry_id).where(ArtifactRow.id == artifact_id)
            )
            if registry_id is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            row = await db_sess.scalar(
                self._select_with_name().where(HuggingFaceRegistryRow.id == registry_id)
            )
            if row is None:
                raise ArtifactRegistryNotFoundError(
                    f"HuggingFace registry not found for artifact {artifact_id}"
                )
            return HuggingFaceRegistrySearchableFields.own.to_data(row)

    async def get_registries_by_ids(
        self, registry_ids: list[uuid.UUID]
    ) -> list[HuggingFaceRegistryData]:
        """
        Get multiple Hugging Face registry entries by their IDs in a single query.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.execute(
                self._select_with_name().where(HuggingFaceRegistryRow.id.in_(registry_ids))
            )
            return [
                HuggingFaceRegistrySearchableFields.own.to_data(row)
                for row in result.scalars().all()
            ]

    async def list_registries(self) -> list[HuggingFaceRegistryData]:
        """
        List all Hugging Face registry entries from the database.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.execute(self._select_with_name())
            return [
                HuggingFaceRegistrySearchableFields.own.to_data(row)
                for row in result.scalars().all()
            ]
