import uuid
from typing import Dict, List

import sqlalchemy as sa

from ai.backend.common.exception import (
    StorageNamespaceNotFoundError,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.object_storage_namespace.creator import StorageNamespaceCreator
from ai.backend.manager.data.object_storage_namespace.types import StorageNamespaceData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for storage namespace repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.OBJECT_STORAGE)


class StorageNamespaceRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
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

    @repository_decorator()
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

    @repository_decorator()
    async def register(self, creator: StorageNamespaceCreator) -> StorageNamespaceData:
        """
        Register a new namespace for the specified storage.
        """
        async with self._db.begin_session() as db_session:
            storage_namespace_data = creator.fields_to_store()
            storage_namespace_row = StorageNamespaceRow(**storage_namespace_data)
            db_session.add(storage_namespace_row)
            await db_session.flush()
            await db_session.refresh(storage_namespace_row)
            return storage_namespace_row.to_dataclass()

    @repository_decorator()
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

    @repository_decorator()
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

    @repository_decorator()
    async def get_all_namespaces_by_storage(self) -> Dict[uuid.UUID, List[str]]:
        """
        Get all namespaces grouped by storage ID.

        Returns:
            Dictionary mapping storage_id to list of namespace names
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(StorageNamespaceRow.storage_id, StorageNamespaceRow.namespace)
            result = await db_session.execute(query)
            rows = result.all()

            namespaces_by_storage: Dict[uuid.UUID, List[str]] = {}
            for row in rows:
                storage_id = row.storage_id
                namespace = row.namespace
                if storage_id not in namespaces_by_storage:
                    namespaces_by_storage[storage_id] = []
                namespaces_by_storage[storage_id].append(namespace)

            return namespaces_by_storage
