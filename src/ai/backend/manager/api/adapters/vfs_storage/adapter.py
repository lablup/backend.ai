"""VFS Storage adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    AdminSearchVFSStoragesInput,
    CreateVFSStorageInput,
    DeleteVFSStorageInput,
    UpdateVFSStorageInput,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    AdminSearchVFSStoragesPayload,
    CreateVFSStoragePayload,
    DeleteVFSStoragePayload,
    UpdateVFSStoragePayload,
    VFSStorageNode,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.models.vfs_storage.conditions import VFSStorageConditions
from ai.backend.manager.models.vfs_storage.creators import VFSStorageCreator
from ai.backend.manager.repositories.vfs_storage.searchers import VFSStorageSearcher
from ai.backend.manager.repositories.vfs_storage.updaters import VFSStorageUpdater
from ai.backend.manager.services.vfs_storage.actions.create import CreateVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.list import ListVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.purge import PurgeVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.search import SearchVFSStoragesAction
from ai.backend.manager.services.vfs_storage.actions.update import UpdateVFSStorageAction
from ai.backend.manager.types import OptionalState

DEFAULT_PAGINATION_LIMIT = 10


class VFSStorageAdapter(BaseAdapter):
    """Adapter for VFS storage domain operations."""

    async def create(self, input: CreateVFSStorageInput) -> CreateVFSStoragePayload:
        """Create a new VFS storage."""
        action_result = await self._processors.vfs_storage.create.run(
            CreateVFSStorageAction(
                creator=VFSStorageCreator(
                    name=input.name,
                    host=input.host,
                    base_path=input.base_path,
                )
            )
        )
        return CreateVFSStoragePayload(
            vfs_storage=self._vfs_storage_data_to_dto(action_result.data)
        )

    async def search(self, input: AdminSearchVFSStoragesInput) -> AdminSearchVFSStoragesPayload:
        """Search VFS storages with pagination."""
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        searcher = VFSStorageSearcher(pagination=pagination, conditions=[], orders=[])
        action_result = await self._processors.vfs_storage.search_vfs_storages.run(
            SearchVFSStoragesAction(searcher=searcher)
        )
        return AdminSearchVFSStoragesPayload(
            items=[self._vfs_storage_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def batch_load_by_ids(self, ids: Sequence[UUID]) -> list[VFSStorageNode | None]:
        """Batch load VFS storages by IDs for DataLoader use.

        Returns VFSStorageNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        searcher = VFSStorageSearcher(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[VFSStorageConditions.by_ids(ids)],
        )
        action_result = await self._processors.vfs_storage.search_vfs_storages.run(
            SearchVFSStoragesAction(searcher=searcher)
        )
        storage_map = {item.id: self._vfs_storage_data_to_dto(item) for item in action_result.items}
        return [storage_map.get(storage_id) for storage_id in ids]

    async def get(self, storage_id: UUID) -> VFSStorageNode:
        """Retrieve a single VFS storage by ID."""
        action_result = await self._processors.vfs_storage.get.run(
            GetVFSStorageAction(storage_id=storage_id)
        )
        return self._vfs_storage_data_to_dto(action_result.data)

    async def list_all(self) -> list[VFSStorageNode]:
        """List all VFS storages without pagination."""
        action_result = await self._processors.vfs_storage.list_storages.run(
            ListVFSStorageAction(searcher=VFSStorageSearcher(pagination=NoPagination()))
        )
        return [self._vfs_storage_data_to_dto(item) for item in action_result.items]

    async def update(self, input: UpdateVFSStorageInput) -> UpdateVFSStoragePayload:
        """Update an existing VFS storage."""
        updater = VFSStorageUpdater(
            storage_id=input.id,
            name=OptionalState.update(input.name)
            if input.name is not None
            else OptionalState.nop(),
            host=OptionalState.update(input.host)
            if input.host is not None
            else OptionalState.nop(),
            base_path=(
                OptionalState.update(input.base_path)
                if input.base_path is not None
                else OptionalState.nop()
            ),
        )
        action_result = await self._processors.vfs_storage.update.run(
            UpdateVFSStorageAction(updater=updater)
        )
        return UpdateVFSStoragePayload(
            vfs_storage=self._vfs_storage_data_to_dto(action_result.data)
        )

    async def delete(self, input: DeleteVFSStorageInput) -> DeleteVFSStoragePayload:
        """Delete a VFS storage."""
        action_result = await self._processors.vfs_storage.purge.run(
            PurgeVFSStorageAction(storage_id=input.id)
        )
        return DeleteVFSStoragePayload(id=action_result.data.id)

    @staticmethod
    def _vfs_storage_data_to_dto(data: VFSStorageData) -> VFSStorageNode:
        return VFSStorageNode(
            id=data.id,
            name=data.name,
            host=data.host,
            base_path=str(data.base_path),
        )
