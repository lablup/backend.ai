from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.data.vfs_storage.types import VFSStorageData, VFSStorageListResult
from ai.backend.manager.errors.vfs_storage import (
    VFSStorageNotFoundError,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.models.vfs_storage.searchable_fields import (
    VFSStorageSearchableFields,
)
from ai.backend.manager.models.vfs_storage.searchers import VFSStorageSearcher
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


class VFSStorageDBSource:
    """Database source for VFS storage operations."""

    _db: ExtendedAsyncSAEngine
    _v2_ops: V2DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops_provider: V2DBOpsProvider) -> None:
        self._db = db
        self._v2_ops = v2_ops_provider

    async def get_by_name(self, storage_name: str) -> VFSStorageData:
        """
        Get an existing VFS storage configuration from the database.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            query = sa.select(VFSStorageRow).where(VFSStorageRow.name == storage_name)
            result = await db_session.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise VFSStorageNotFoundError(f"VFS storage with name {storage_name} not found.")
            return VFSStorageSearchableFields.own.to_data(row)

    async def get_by_id(self, storage_id: uuid.UUID) -> VFSStorageData:
        """
        Get an existing VFS storage configuration from the database by ID.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            query = sa.select(VFSStorageRow).where(VFSStorageRow.id == storage_id)
            result = await db_session.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise VFSStorageNotFoundError(f"VFS storage with ID {storage_id} not found.")
            return VFSStorageSearchableFields.own.to_data(row)

    async def list_vfs_storages(self) -> list[VFSStorageData]:
        """
        List all VFS storage configurations from the database.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            query = sa.select(VFSStorageRow)
            result = await db_session.execute(query)
            rows = result.scalars().all()
            return [VFSStorageSearchableFields.own.to_data(row) for row in rows]

    async def search(
        self,
        searcher: VFSStorageSearcher,
    ) -> VFSStorageListResult:
        """Searches VFS storages with total count."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(searcher)
        return VFSStorageListResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
