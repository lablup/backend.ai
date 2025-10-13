import uuid

import sqlalchemy as sa

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.data.vfs_storage.creator import VFSStorageCreator
from ai.backend.manager.data.vfs_storage.modifier import VFSStorageModifier
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.errors.vfs_storage import (
    VFSStorageNotFoundError,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage import VFSStorageRow

vfs_storage_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.VFS_STORAGE_REPOSITORY)
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


class VFSStorageRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @vfs_storage_repository_resilience.apply()
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

    @vfs_storage_repository_resilience.apply()
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

    @vfs_storage_repository_resilience.apply()
    async def create(self, creator: VFSStorageCreator) -> VFSStorageData:
        """
        Create a new VFS storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            vfs_storage_data = creator.fields_to_store()
            vfs_storage_row = VFSStorageRow(**vfs_storage_data)
            db_session.add(vfs_storage_row)
            await db_session.flush()
            await db_session.refresh(vfs_storage_row)
            return vfs_storage_row.to_dataclass()

    @vfs_storage_repository_resilience.apply()
    async def update(self, storage_id: uuid.UUID, modifier: VFSStorageModifier) -> VFSStorageData:
        """
        Update an existing VFS storage configuration in the database.
        """
        async with self._db.begin_session() as db_session:
            data = modifier.fields_to_update()
            update_stmt = (
                sa.update(VFSStorageRow)
                .where(VFSStorageRow.id == storage_id)
                .values(**data)
                .returning(*sa.select(VFSStorageRow).selected_columns)
            )
            stmt = sa.select(VFSStorageRow).from_statement(update_stmt)
            row: VFSStorageRow = (await db_session.execute(stmt)).scalars().one()

            return row.to_dataclass()

    @vfs_storage_repository_resilience.apply()
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

    @vfs_storage_repository_resilience.apply()
    async def list_vfs_storages(self) -> list[VFSStorageData]:
        """
        List all VFS storage configurations from the database.
        """
        async with self._db.begin_session() as db_session:
            query = sa.select(VFSStorageRow)
            result = await db_session.execute(query)
            rows: list[VFSStorageRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]
