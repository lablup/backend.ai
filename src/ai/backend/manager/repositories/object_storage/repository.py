import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.exception import (
    StorageNamespaceNotFoundError,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
from ai.backend.manager.data.object_storage.modifier import ObjectStorageModifier
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.object_storage_namespace.creator import ObjectStorageNamespaceCreator
from ai.backend.manager.data.object_storage_namespace.types import ObjectStorageNamespaceData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.object_storage import (
    ObjectStorageBucketNotFoundError,
    ObjectStorageNotFoundError,
)
from ai.backend.manager.models.object_storage import ObjectStorageNamespaceRow, ObjectStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for user repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.OBJECT_STORAGE)


class ObjectStorageRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
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

    @repository_decorator()
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

    @repository_decorator()
    async def get_by_namespace_id(self, storage_namespace_id: uuid.UUID) -> ObjectStorageData:
        """
        Get an existing object storage configuration from the database by ID.
        """
        async with self._db.begin_session() as db_session:
            query = (
                sa.select(ObjectStorageNamespaceRow)
                .where(ObjectStorageNamespaceRow.id == storage_namespace_id)
                .options(selectinload(ObjectStorageNamespaceRow.object_storage_row))
            )
            result = await db_session.execute(query)
            row: ObjectStorageNamespaceRow = result.scalar_one_or_none()
            if row is None:
                raise ObjectStorageNotFoundError(
                    f"Object storage with namespace ID {storage_namespace_id} not found."
                )
            return row.object_storage_row.to_dataclass()

    @repository_decorator()
    async def get_storage_namespace(
        self, storage_id: uuid.UUID, bucket_name: str
    ) -> ObjectStorageNamespaceData:
        """
        Get an existing object storage namespace from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageNamespaceRow).where(
                ObjectStorageNamespaceRow.storage_id == storage_id,
                ObjectStorageNamespaceRow.bucket == bucket_name,
            )
            result = await db_session.execute(query)
            row: ObjectStorageNamespaceRow = result.scalar_one_or_none()
            if row is None:
                raise StorageNamespaceNotFoundError(
                    f"Object storage namespace with bucket_name {bucket_name} not found."
                )
            return row.to_dataclass()

    @repository_decorator()
    async def get_storage_namespace_by_id(
        self, storage_namespace_id: uuid.UUID
    ) -> ObjectStorageNamespaceData:
        """
        Get an existing object storage namespace from the database by ID.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageNamespaceRow).where(
                ObjectStorageNamespaceRow.id == storage_namespace_id
            )
            result = await db_session.execute(query)
            row: ObjectStorageNamespaceRow = result.scalar_one_or_none()
            if row is None:
                raise StorageNamespaceNotFoundError(
                    f"Object storage namespace ID {storage_namespace_id} not found."
                )
            return row.to_dataclass()

    @repository_decorator()
    async def create(self, creator: ObjectStorageCreator) -> ObjectStorageData:
        """
        Create a new object storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            object_storage_data = creator.fields_to_store()
            object_storage_row = ObjectStorageRow(**object_storage_data)
            db_session.add(object_storage_row)
            await db_session.flush()
            await db_session.refresh(object_storage_row)
            return object_storage_row.to_dataclass()

    @repository_decorator()
    async def update(
        self, storage_id: uuid.UUID, modifier: ObjectStorageModifier
    ) -> ObjectStorageData:
        """
        Update an existing object storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            data = modifier.fields_to_update()
            update_stmt = (
                sa.update(ObjectStorageRow)
                .where(ObjectStorageRow.id == storage_id)
                .values(**data)
                .returning(*sa.select(ObjectStorageRow).selected_columns)
            )
            stmt = sa.select(ObjectStorageRow).from_statement(update_stmt)
            row: ObjectStorageRow = (await db_session.execute(stmt)).scalars().one()

            return row.to_dataclass()

    @repository_decorator()
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

    @repository_decorator()
    async def list_object_storages(self) -> list[ObjectStorageData]:
        """
        List all object storage configurations from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageRow)
            result = await db_session.execute(query)
            rows: list[ObjectStorageRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @repository_decorator()
    async def register_bucket(
        self, creator: ObjectStorageNamespaceCreator
    ) -> ObjectStorageNamespaceData:
        """
        Register a new bucket for the specified object storage.
        """
        async with self._db.begin_session() as db_session:
            object_storage_namespace_data = creator.fields_to_store()
            object_storage_namespace_row = ObjectStorageNamespaceRow(
                **object_storage_namespace_data
            )
            db_session.add(object_storage_namespace_row)
            await db_session.flush()
            await db_session.refresh(object_storage_namespace_row)
            return object_storage_namespace_row.to_dataclass()

    @repository_decorator()
    async def unregister_bucket(self, storage_id: uuid.UUID, bucket_name: str) -> uuid.UUID:
        """
        Unregister a bucket from the specified object storage.
        """
        async with self._db.begin_session() as db_session:
            delete_query = (
                sa.delete(ObjectStorageNamespaceRow)
                .where(
                    ObjectStorageNamespaceRow.storage_id == storage_id,
                    ObjectStorageNamespaceRow.bucket == bucket_name,
                )
                .returning(ObjectStorageNamespaceRow.storage_id)
            )
            result = await db_session.execute(delete_query)
            deleted_storage_id = result.scalar()
            if deleted_storage_id is None:
                raise ObjectStorageBucketNotFoundError()
            return deleted_storage_id

    @repository_decorator()
    async def get_buckets(self, storage_id: uuid.UUID) -> list[ObjectStorageNamespaceData]:
        """
        Get all buckets for the specified object storage.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageNamespaceRow).where(
                ObjectStorageNamespaceRow.storage_id == storage_id
            )
            result = await db_session.execute(query)
            rows: list[ObjectStorageNamespaceRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @repository_decorator()
    async def get_all_buckets_by_storage(self) -> dict[uuid.UUID, list[str]]:
        """
        Get all buckets grouped by storage ID.

        Returns:
            Dictionary mapping storage_id to list of bucket names
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(
                ObjectStorageNamespaceRow.storage_id, ObjectStorageNamespaceRow.bucket
            )
            result = await db_session.execute(query)
            rows = result.all()

            buckets_by_storage: dict[uuid.UUID, list[str]] = {}
            for row in rows:
                storage_id = row.storage_id
                bucket_name = row.bucket
                if storage_id not in buckets_by_storage:
                    buckets_by_storage[storage_id] = []
                buckets_by_storage[storage_id].append(bucket_name)

            return buckets_by_storage
