from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.exception import (
    StorageNamespaceNotFoundError,
)
from ai.backend.manager.data.storage_namespace.types import (
    StorageNamespaceData,
)
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


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
        async with self._db.begin_readonly_session_read_committed() as db_session:
            query = sa.select(StorageNamespaceRow).where(
                StorageNamespaceRow.storage_id == storage_id,
                StorageNamespaceRow.namespace == namespace,
            )
            result = await db_session.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise StorageNamespaceNotFoundError(
                    f"Storage namespace with namespace {namespace} not found."
                )
            return row.to_dataclass()

    async def get_by_id(self, storage_namespace_id: uuid.UUID) -> StorageNamespaceData:
        """
        Get an existing storage namespace from the database by ID.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            query = sa.select(StorageNamespaceRow).where(
                StorageNamespaceRow.id == storage_namespace_id
            )
            result = await db_session.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise StorageNamespaceNotFoundError(
                    f"Storage namespace ID {storage_namespace_id} not found."
                )
            return row.to_dataclass()
