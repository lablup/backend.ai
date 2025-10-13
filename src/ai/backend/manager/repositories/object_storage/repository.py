import uuid

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.exception import (
    BackendAIError,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.object_storage.creator import ObjectStorageCreator
from ai.backend.manager.data.object_storage.modifier import ObjectStorageModifier
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.errors.object_storage import (
    ObjectStorageNotFoundError,
)
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

object_storage_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.OBJECT_STORAGE_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class ObjectStorageRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @object_storage_repository_resilience.apply()
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

    @object_storage_repository_resilience.apply()
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

    @object_storage_repository_resilience.apply()
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

    @object_storage_repository_resilience.apply()
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

    @object_storage_repository_resilience.apply()
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

    @object_storage_repository_resilience.apply()
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

    @object_storage_repository_resilience.apply()
    async def list_object_storages(self) -> list[ObjectStorageData]:
        """
        List all object storage configurations from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(ObjectStorageRow)
            result = await db_session.execute(query)
            rows: list[ObjectStorageRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
