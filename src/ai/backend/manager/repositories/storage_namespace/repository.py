import uuid

import sqlalchemy as sa

from ai.backend.common.exception import (
    BackendAIError,
    StorageNamespaceNotFoundError,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.storage_namespace.creator import StorageNamespaceCreator
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

storage_namespace_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.STORAGE_NAMESPACE_REPOSITORY)
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


class StorageNamespaceRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @storage_namespace_repository_resilience.apply()
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

    @storage_namespace_repository_resilience.apply()
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

    @storage_namespace_repository_resilience.apply()
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

    @storage_namespace_repository_resilience.apply()
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

    @storage_namespace_repository_resilience.apply()
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

    @storage_namespace_repository_resilience.apply()
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
