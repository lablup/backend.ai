from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
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
    async def create(self, data: ObjectStorageCreator) -> ObjectStorageData:
        """
        Create a new object storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            object_storage_row = ObjectStorageRow.from_input(data.fields_to_store())
            db_session.add(object_storage_row)
            await db_session.flush()
            await db_session.refresh(object_storage_row)
            return object_storage_row.to_data()
