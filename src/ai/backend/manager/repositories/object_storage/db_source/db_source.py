from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.object_storage.types import ObjectStorageData, ObjectStorageListResult
from ai.backend.manager.errors.object_storage import (
    ObjectStorageNotFoundError,
)
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater


class ObjectStorageDBSource:
    """Database source for object storage operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_name(self, storage_name: str) -> ObjectStorageData:
        """
        Get an existing object storage configuration from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageRow).where(ObjectStorageRow.name == storage_name)
            result = await db_session.execute(query)
            row: ObjectStorageRow = result.scalar_one_or_none()
            if row is None:
                raise ObjectStorageNotFoundError(
                    f"Object storage with name {storage_name} not found."
                )
            return row.to_dataclass()

    async def get_by_id(self, storage_id: uuid.UUID) -> ObjectStorageData:
        """
        Get an existing object storage configuration from the database by ID.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageRow).where(ObjectStorageRow.id == storage_id)
            result = await db_session.execute(query)
            row: ObjectStorageRow = result.scalar_one_or_none()
            if row is None:
                raise ObjectStorageNotFoundError(f"Object storage with ID {storage_id} not found.")
            return row.to_dataclass()

    async def get_by_namespace_id(self, storage_namespace_id: uuid.UUID) -> ObjectStorageData:
        """
        Get an existing object storage configuration from the database by ID.
        """
        async with self._db.begin_session() as db_session:
            query = (
                sa.select(StorageNamespaceRow)
                .where(StorageNamespaceRow.id == storage_namespace_id)
                .options(selectinload(StorageNamespaceRow.object_storage_row))
            )
            result = await db_session.execute(query)
            row: StorageNamespaceRow = result.scalar_one_or_none()
            if row is None:
                raise ObjectStorageNotFoundError(
                    f"Object storage with namespace ID {storage_namespace_id} not found."
                )
            return row.object_storage_row.to_dataclass()

    async def create(self, creator: Creator[ObjectStorageRow]) -> ObjectStorageData:
        """
        Create a new object storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            creator_result = await execute_creator(db_session, creator)
            return creator_result.row.to_dataclass()

    async def update(self, updater: Updater[ObjectStorageRow]) -> ObjectStorageData:
        """
        Update an existing object storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            result = await execute_updater(db_session, updater)
            if result is None:
                raise ObjectStorageNotFoundError(
                    f"Object storage with ID {updater.pk_value} not found."
                )
            return result.row.to_dataclass()

    async def delete(self, storage_id: uuid.UUID) -> uuid.UUID:
        """
        Delete an existing object storage configuration from the database.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(ObjectStorageRow)
                .where(ObjectStorageRow.id == storage_id)
                .returning(ObjectStorageRow.id)
            )
            result = await db_session.execute(delete_query)
            deleted_id = result.scalar()
            return deleted_id

    async def list_object_storages(self) -> list[ObjectStorageData]:
        """
        List all object storage configurations from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageRow)
            result = await db_session.execute(query)
            rows: list[ObjectStorageRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def search(
        self,
        querier: BatchQuerier,
    ) -> ObjectStorageListResult:
        """Searches Object storages with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ObjectStorageRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.ObjectStorageRow.to_dataclass() for row in result.rows]

            return ObjectStorageListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
