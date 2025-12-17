from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.exception import (
    StorageNamespaceNotFoundError,
)
from ai.backend.manager.data.storage_namespace.types import (
    StorageNamespaceData,
    StorageNamespaceListResult,
)
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.creator import Creator, execute_creator


class StorageNamespaceDBSource:
    """Database source for storage namespace operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_storage_and_namespace(
        self, storage_id: uuid.UUID, namespace: str
    ) -> StorageNamespaceData:
        """
        Get an existing storage namespace from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(StorageNamespaceRow).where(
                StorageNamespaceRow.storage_id == storage_id,
                StorageNamespaceRow.namespace == namespace,
            )
            result = await db_session.execute(query)
            row: StorageNamespaceRow = result.scalar_one_or_none()
            if row is None:
                raise StorageNamespaceNotFoundError(
                    f"Storage namespace with namespace {namespace} not found."
                )
            return row.to_dataclass()

    async def get_by_id(self, storage_namespace_id: uuid.UUID) -> StorageNamespaceData:
        """
        Get an existing storage namespace from the database by ID.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(StorageNamespaceRow).where(
                StorageNamespaceRow.id == storage_namespace_id
            )
            result = await db_session.execute(query)
            row: StorageNamespaceRow = result.scalar_one_or_none()
            if row is None:
                raise StorageNamespaceNotFoundError(
                    f"Storage namespace ID {storage_namespace_id} not found."
                )
            return row.to_dataclass()

    async def register(self, creator: Creator[StorageNamespaceRow]) -> StorageNamespaceData:
        """
        Register a new namespace for the specified storage.
        """
        async with self._db.begin_session() as db_session:
            creator_result = await execute_creator(db_session, creator)
            return creator_result.row.to_dataclass()

    async def unregister(self, storage_id: uuid.UUID, namespace: str) -> uuid.UUID:
        """
        Unregister a namespace from the specified storage.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(StorageNamespaceRow)
                .where(
                    StorageNamespaceRow.storage_id == storage_id,
                    StorageNamespaceRow.namespace == namespace,
                )
                .returning(StorageNamespaceRow.storage_id)
            )
            result = await db_session.execute(delete_query)
            deleted_storage_id = result.scalar()
            if deleted_storage_id is None:
                raise StorageNamespaceNotFoundError()
            return deleted_storage_id

    async def get_namespaces(self, storage_id: uuid.UUID) -> list[StorageNamespaceData]:
        """
        Get all namespaces for the specified storage.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(StorageNamespaceRow).where(
                StorageNamespaceRow.storage_id == storage_id
            )
            result = await db_session.execute(query)
            rows: list[StorageNamespaceRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    async def get_all_namespaces_by_storage(self) -> dict[uuid.UUID, list[str]]:
        """
        Get all namespaces grouped by storage ID.

        Returns:
            Dictionary mapping storage_id to list of namespace names
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(StorageNamespaceRow.storage_id, StorageNamespaceRow.namespace)
            result = await db_session.execute(query)
            rows = result.all()

            namespaces_by_storage: dict[uuid.UUID, list[str]] = {}
            for row in rows:
                storage_id = row.storage_id
                namespace = row.namespace
                if storage_id not in namespaces_by_storage:
                    namespaces_by_storage[storage_id] = []
                namespaces_by_storage[storage_id].append(namespace)

            return namespaces_by_storage

    async def search(
        self,
        querier: BatchQuerier,
    ) -> StorageNamespaceListResult:
        """Searches storage namespaces with total count."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(StorageNamespaceRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.StorageNamespaceRow.to_dataclass() for row in result.rows]

            return StorageNamespaceListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
