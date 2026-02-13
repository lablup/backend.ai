from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.data.artifact_storages.types import ArtifactStorageData
from ai.backend.manager.errors.artifact_storage import ArtifactStorageNotFoundError
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.updater import Updater, execute_updater


class ArtifactStorageDBSource:
    """Database source for artifact storage operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_id(self, storage_id: uuid.UUID) -> ArtifactStorageData:
        """
        Get an existing artifact storage configuration from the database by ID.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ArtifactStorageRow).where(ArtifactStorageRow.id == storage_id)
            result = await db_session.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactStorageNotFoundError(
                    f"Artifact storage with ID {storage_id} not found."
                )
            return row.to_dataclass()

    async def get_by_storage_id(self, storage_id: uuid.UUID) -> ArtifactStorageData:
        """
        Get an existing artifact storage configuration from the database by storage_id.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ArtifactStorageRow).where(ArtifactStorageRow.storage_id == storage_id)
            result = await db_session.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactStorageNotFoundError(
                    f"Artifact storage with storage_id {storage_id} not found."
                )
            return row.to_dataclass()

    async def update(
        self,
        updater: Updater[ArtifactStorageRow],
    ) -> ArtifactStorageData:
        """
        Update an existing artifact storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            # Execute update (may return None if no values to update, which is fine)
            await execute_updater(db_session, updater)

            artifact_storage_id = uuid.UUID(str(updater.pk_value))
            # Re-query to get the updated row
            query = sa.select(ArtifactStorageRow).where(
                ArtifactStorageRow.id == artifact_storage_id
            )
            row_result = await db_session.execute(query)
            row = row_result.scalar_one_or_none()
            if row is None:
                raise ArtifactStorageNotFoundError(
                    f"Artifact storage with ID {artifact_storage_id} not found."
                )
            return row.to_dataclass()
