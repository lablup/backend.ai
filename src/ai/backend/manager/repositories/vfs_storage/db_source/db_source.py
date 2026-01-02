from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.data.vfs_storage.types import VFSStorageData, VFSStorageListResult
from ai.backend.manager.errors.vfs_storage import (
    VFSStorageNotFoundError,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater


class VFSStorageDBSource:
    """Database source for VFS storage operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_name(self, storage_name: str) -> VFSStorageData:
        """
        Get an existing VFS storage configuration from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(VFSStorageRow).where(VFSStorageRow.name == storage_name)
            result = await db_session.execute(query)
            row: VFSStorageRow = result.scalar_one_or_none()
            if row is None:
                raise VFSStorageNotFoundError(f"VFS storage with name {storage_name} not found.")
            return row.to_dataclass()

    async def get_by_id(self, storage_id: uuid.UUID) -> VFSStorageData:
        """
        Get an existing VFS storage configuration from the database by ID.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(VFSStorageRow).where(VFSStorageRow.id == storage_id)
            result = await db_session.execute(query)
            row: VFSStorageRow = result.scalar_one_or_none()
            if row is None:
                raise VFSStorageNotFoundError(f"VFS storage with ID {storage_id} not found.")
            return row.to_dataclass()

    async def create(self, creator: Creator[VFSStorageRow]) -> VFSStorageData:
        """
        Create a new VFS storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            creator_result = await execute_creator(db_session, creator)
            return creator_result.row.to_dataclass()

    async def update(self, updater: Updater[VFSStorageRow]) -> VFSStorageData:
        """
        Update an existing VFS storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            result = await execute_updater(db_session, updater)
            if result is None:
                raise VFSStorageNotFoundError(f"VFS storage with ID {updater.pk_value} not found.")
            return result.row.to_dataclass()

    async def delete(self, storage_id: uuid.UUID) -> uuid.UUID:
        """
        Delete an existing VFS storage configuration from the database.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(VFSStorageRow)
                .where(VFSStorageRow.id == storage_id)
                .returning(VFSStorageRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_id = result.scalar()
            return deleted_id

    async def list_vfs_storages(self) -> list[VFSStorageData]:
        """
        List all VFS storage configurations from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(VFSStorageRow)
            result = await db_session.execute(query)
            rows: list[VFSStorageRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def search(
        self,
        querier: BatchQuerier,
    ) -> VFSStorageListResult:
        """Searches VFS storages with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(VFSStorageRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.VFSStorageRow.to_dataclass() for row in result.rows]

            return VFSStorageListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
