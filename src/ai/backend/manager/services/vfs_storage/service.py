import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.vfs_storage.actions.create import (
    CreateVFSStorageAction,
    CreateVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.delete import (
    DeleteVFSStorageAction,
    DeleteVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.get import (
    GetVFSStorageAction,
    GetVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.list import (
    ListVFSStorageAction,
    ListVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.search import (
    SearchVFSStoragesAction,
    SearchVFSStoragesActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.update import (
    UpdateVFSStorageAction,
    UpdateVFSStorageActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class VFSStorageService:
    _vfs_storage_repository: VFSStorageRepository

    def __init__(
        self,
        vfs_storage_repository: VFSStorageRepository,
    ) -> None:
        self._vfs_storage_repository = vfs_storage_repository

    async def create(self, action: CreateVFSStorageAction) -> CreateVFSStorageActionResult:
        """
        Create a new VFS storage.
        """
        log.info("Creating VFS storage with data: {}", action.creator)
        storage_data = await self._vfs_storage_repository.create(action.creator)
        return CreateVFSStorageActionResult(result=storage_data)

    async def update(self, action: UpdateVFSStorageAction) -> UpdateVFSStorageActionResult:
        """
        Update an existing VFS storage.
        """
        log.info("Updating VFS storage with id: {}", action.updater.pk_value)
        storage_data = await self._vfs_storage_repository.update(action.updater)
        return UpdateVFSStorageActionResult(result=storage_data)

    async def delete(self, action: DeleteVFSStorageAction) -> DeleteVFSStorageActionResult:
        """
        Delete an existing VFS storage.
        """
        log.info("Deleting VFS storage with id: {}", action.storage_id)
        storage_data = await self._vfs_storage_repository.delete(action.storage_id)
        return DeleteVFSStorageActionResult(deleted_storage_id=storage_data)

    async def get(self, action: GetVFSStorageAction) -> GetVFSStorageActionResult:
        """
        Get an existing VFS storage by ID.
        """
        log.info("Getting VFS storage with id: {}", action.storage_id)
        if action.storage_id:
            storage_data = await self._vfs_storage_repository.get_by_id(action.storage_id)
        elif action.storage_name:
            storage_data = await self._vfs_storage_repository.get_by_name(action.storage_name)
        else:
            raise GenericBadRequest("Either storage_id or storage_name must be provided")

        return GetVFSStorageActionResult(result=storage_data)

    async def list(self, action: ListVFSStorageAction) -> ListVFSStorageActionResult:
        """
        List all VFS storages.
        """
        log.info("Listing VFS storages")
        storage_data_list = await self._vfs_storage_repository.list_vfs_storages()
        return ListVFSStorageActionResult(data=storage_data_list)

    async def search(self, action: SearchVFSStoragesAction) -> SearchVFSStoragesActionResult:
        """
        Search VFS storages with pagination and filtering.
        """
        log.info("Searching VFS storages with querier: {}", action.querier)
        result = await self._vfs_storage_repository.search(action.querier)
        return SearchVFSStoragesActionResult(
            storages=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
