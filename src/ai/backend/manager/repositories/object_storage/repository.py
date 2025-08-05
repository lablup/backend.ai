import uuid

import sqlalchemy as sa

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
from ai.backend.manager.data.object_storage.modifier import ObjectStorageModifier
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for user repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.OBJECT_STORAGE)


class ObjectStorageRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get(self, storage_name: str) -> ObjectStorageData:
        """
        Get an existing object storage configuration from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageRow).where(ObjectStorageRow.name == storage_name)
            result = await db_session.execute(query)
            row: ObjectStorageRow = result.scalar_one_or_none()
            if row is None:
                raise ValueError(f"Object storage with name {storage_name} not found.")
            return row.to_data()

    @repository_decorator()
    async def create(self, creator: ObjectStorageCreator) -> ObjectStorageData:
        """
        Create a new object storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            object_storage_row = ObjectStorageRow.from_input(creator.fields_to_store())
            db_session.add(object_storage_row)
            await db_session.flush()
            await db_session.refresh(object_storage_row)
            return object_storage_row.to_data()

    @repository_decorator()
    async def update(self, modifier: ObjectStorageModifier) -> ObjectStorageData:
        """
        Update an existing object storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            data = modifier.fields_to_update()
            update_query = (
                sa.update(ObjectStorageRow)
                .values(data)
                .where(ObjectStorageRow.name == modifier.name)
                .returning(ObjectStorageRow)
            )
            result = await db_session.execute(update_query)
            row: ObjectStorageRow = result.first()
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
