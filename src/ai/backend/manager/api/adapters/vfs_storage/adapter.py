"""VFS Storage adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.common.dto.manager.v2.common import PartialBulkFailure, PartialBulkPayload
from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    AdminSearchVFSStoragesInput,
    CreateVFSStorageInput,
    PartialBulkPurgeVFSStoragesInput,
    PartialBulkUpdateVFSStoragesInput,
    UpdateVFSStorageInput,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    AdminSearchVFSStoragesPayload,
    CreateVFSStoragePayload,
    PurgeVFSStoragePayload,
    UpdateVFSStoragePayload,
    VFSStorageNode,
)
from ai.backend.manager.actions.v2.bulk.result import PartialBulkResult
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.models.vfs_storage.creators import VFSStorageCreator
from ai.backend.manager.models.vfs_storage.searchers import VFSStorageSearcher
from ai.backend.manager.models.vfs_storage.updaters import VFSStorageUpdater
from ai.backend.manager.services.vfs_storage.actions.bulk_get import BulkGetVFSStoragesAction
from ai.backend.manager.services.vfs_storage.actions.create import CreateVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.get import GetVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.list import ListVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.partial_bulk_purge_vfs_storages import (
    PartialBulkPurgeVFSStoragesAction,
)
from ai.backend.manager.services.vfs_storage.actions.partial_bulk_update_vfs_storages import (
    PartialBulkUpdateVFSStoragesAction,
)
from ai.backend.manager.services.vfs_storage.actions.purge import PurgeVFSStorageAction
from ai.backend.manager.services.vfs_storage.actions.search import SearchVFSStoragesAction
from ai.backend.manager.services.vfs_storage.actions.update import UpdateVFSStorageAction
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors
from ai.backend.manager.types import OptionalState

DEFAULT_PAGINATION_LIMIT = 10


class VFSStorageAdapter(BaseAdapter):
    """Adapter for VFS storage domain operations."""

    _vfs_storage: VFSStorageProcessors

    def __init__(self, vfs_storage: VFSStorageProcessors) -> None:
        self._vfs_storage = vfs_storage

    async def create(self, input: CreateVFSStorageInput) -> CreateVFSStoragePayload:
        """Create a new VFS storage."""
        action_result = await self._vfs_storage.global_create.run(
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
        action_result = await self._vfs_storage.global_search_vfs_storages.run(
            SearchVFSStoragesAction(searcher=GlobalSearcher(used_by=(), searcher=searcher))
        )
        return AdminSearchVFSStoragesPayload(
            items=[self._vfs_storage_data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def batch_load_by_ids(
        self, ids: Sequence[VFSStorageID]
    ) -> list[VFSStorageNode | Exception | None]:
        """Batch load VFS storages by id for DataLoader use.

        One answer per id in the given order: the node, ``None`` for an id matching no
        row, and the denial for one the caller may not read.
        """
        if not ids:
            return []
        entity_ids = [VFSStorageID(value) for value in ids]
        result = await self._vfs_storage.bulk_get.run(BulkGetVFSStoragesAction(ids=entity_ids))
        return [
            self._vfs_storage_data_to_dto(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def get(self, storage_id: UUID) -> VFSStorageNode:
        """Retrieve a single VFS storage by ID."""
        action_result = await self._vfs_storage.get.run(
            GetVFSStorageAction(storage_id=VFSStorageID(storage_id))
        )
        return self._vfs_storage_data_to_dto(action_result.data)

    async def list_all(self) -> list[VFSStorageNode]:
        """List all VFS storages without pagination."""
        action_result = await self._vfs_storage.global_list_storages.run(
            ListVFSStorageAction(
                searcher=GlobalSearcher(
                    used_by=(), searcher=VFSStorageSearcher(pagination=NoPagination())
                )
            )
        )
        return [self._vfs_storage_data_to_dto(item) for item in action_result.items]

    async def update(
        self, storage_id: VFSStorageID, input: UpdateVFSStorageInput
    ) -> UpdateVFSStoragePayload:
        """Update an existing VFS storage. The ID the input carries is not read."""
        action_result = await self._vfs_storage.update.run(
            UpdateVFSStorageAction(updater=self._to_updater(storage_id, input))
        )
        return UpdateVFSStoragePayload(
            vfs_storage=self._vfs_storage_data_to_dto(action_result.data)
        )

    async def purge(self, storage_id: VFSStorageID) -> PurgeVFSStoragePayload:
        """Permanently remove a VFS storage."""
        action_result = await self._vfs_storage.purge.run(
            PurgeVFSStorageAction(storage_id=storage_id)
        )
        return PurgeVFSStoragePayload(id=action_result.data.id, entity_id=action_result.data.id)

    async def partial_bulk_update(
        self, input: PartialBulkUpdateVFSStoragesInput
    ) -> PartialBulkPayload[VFSStorageNode]:
        """Update several VFS storages, answering for each one."""
        result = await self._vfs_storage.partial_bulk_update.run(
            PartialBulkUpdateVFSStoragesAction(
                updaters=[self._to_updater(VFSStorageID(item.id), item) for item in input.items]
            )
        )
        return self._to_partial_bulk_payload(result)

    async def partial_bulk_purge(
        self, input: PartialBulkPurgeVFSStoragesInput
    ) -> PartialBulkPayload[VFSStorageNode]:
        """Permanently remove several VFS storages, answering for each one."""
        result = await self._vfs_storage.partial_bulk_purge.run(
            PartialBulkPurgeVFSStoragesAction(
                ids=[VFSStorageID(storage_id) for storage_id in input.ids]
            )
        )
        return self._to_partial_bulk_payload(result)

    def _to_updater(
        self, storage_id: VFSStorageID, input: UpdateVFSStorageInput
    ) -> VFSStorageUpdater:
        return VFSStorageUpdater(
            storage_id=storage_id,
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

    def _to_partial_bulk_payload(
        self, result: PartialBulkResult[VFSStorageData]
    ) -> PartialBulkPayload[VFSStorageNode]:
        return PartialBulkPayload[VFSStorageNode](
            successes=[
                self._vfs_storage_data_to_dto(item.value)
                for item in result.items
                if item.value is not None
            ],
            failed=[
                PartialBulkFailure(id=item.entity_id, message=str(item.error))
                for item in result.items
                if item.error is not None
            ],
        )

    @staticmethod
    def _vfs_storage_data_to_dto(data: VFSStorageData) -> VFSStorageNode:
        return VFSStorageNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            host=data.host,
            base_path=str(data.base_path),
        )
