"""VFS Storage adapter bridging DTOs and Processors."""

from __future__ import annotations

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
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination, Updater
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.vfs_storage import VFSStorageCreatorSpec
from ai.backend.manager.repositories.vfs_storage.updaters import VFSStorageUpdaterSpec
from ai.backend.manager.services.vfs_storage.actions.create import CreateVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.delete import DeleteVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.search import SearchVFSStoragesAction
from ai.backend.manager.services.vfs_storage.actions.update import UpdateVFSStorageAction
from ai.backend.manager.types import OptionalState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class VFSStorageAdapter(BaseAdapter):
    """Adapter for VFS storage domain operations."""

    async def create(self, input: CreateVFSStorageInput) -> CreateVFSStoragePayload:
        """Create a new VFS storage."""
        action_result = await self._processors.vfs_storage.create.wait_for_complete(
            CreateVFSStorageAction(
                creator=Creator(
                    spec=VFSStorageCreatorSpec(
                        name=input.name,
                        host=input.host,
                        base_path=input.base_path,
                    )
                )
            )
        )
        return CreateVFSStoragePayload(
            vfs_storage=self._vfs_storage_data_to_dto(action_result.result)
        )

    async def search(self, input: AdminSearchVFSStoragesInput) -> AdminSearchVFSStoragesPayload:
        """Search VFS storages with pagination."""
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        querier = BatchQuerier(conditions=[], orders=[], pagination=pagination)
        action_result = await self._processors.vfs_storage.search_vfs_storages.wait_for_complete(
            SearchVFSStoragesAction(querier=querier)
        )
        return AdminSearchVFSStoragesPayload(
            items=[self._vfs_storage_data_to_dto(item) for item in action_result.storages],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, storage_id: UUID) -> VFSStorageNode:
        """Retrieve a single VFS storage by ID."""
        action_result = await self._processors.vfs_storage.get.wait_for_complete(
            GetVFSStorageAction(storage_id=storage_id)
        )
        return self._vfs_storage_data_to_dto(action_result.result)

    async def update(self, input: UpdateVFSStorageInput) -> UpdateVFSStoragePayload:
        """Update an existing VFS storage."""
        spec = VFSStorageUpdaterSpec(
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
        action_result = await self._processors.vfs_storage.update.wait_for_complete(
            UpdateVFSStorageAction(updater=Updater(spec=spec, pk_value=input.id))
        )
        return UpdateVFSStoragePayload(
            vfs_storage=self._vfs_storage_data_to_dto(action_result.result)
        )

    async def delete(self, input: DeleteVFSStorageInput) -> DeleteVFSStoragePayload:
        """Delete a VFS storage."""
        action_result = await self._processors.vfs_storage.delete.wait_for_complete(
            DeleteVFSStorageAction(storage_id=input.id)
        )
        return DeleteVFSStoragePayload(id=action_result.deleted_storage_id)

    @staticmethod
    def _vfs_storage_data_to_dto(data: VFSStorageData) -> VFSStorageNode:
        return VFSStorageNode(
            id=data.id,
            name=data.name,
            host=data.host,
            base_path=str(data.base_path),
        )
