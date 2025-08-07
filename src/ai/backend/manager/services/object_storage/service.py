import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.services.object_storage.actions.create import (
    CreateObjectStorageAction,
    CreateObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.delete import (
    DeleteObjectStorageAction,
    DeleteObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.get import (
    GetObjectStorageAction,
    GetObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.list import (
    ListObjectStorageAction,
    ListObjectStorageActionResult,
)
from ai.backend.manager.services.object_storage.actions.update import (
    UpdateObjectStorageAction,
    UpdateObjectStorageActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ObjectStorageService:
    _object_storage_repository: ObjectStorageRepository

    def __init__(self, object_storage_repository: ObjectStorageRepository) -> None:
        self._object_storage_repository = object_storage_repository

    async def create(self, action: CreateObjectStorageAction) -> CreateObjectStorageActionResult:
        """
        Create a new object storage.
        """
        log.info("Creating object storage with data: {}", action.creator.fields_to_store())
        storage_data = await self._object_storage_repository.create(action.creator)
        return CreateObjectStorageActionResult(result=storage_data)

    async def update(self, action: UpdateObjectStorageAction) -> UpdateObjectStorageActionResult:
        """
        Update an existing object storage.
        """
        log.info("Updating object storage with data: {}", action.modifier.fields_to_update())
        storage_data = await self._object_storage_repository.update(action.id, action.modifier)
        return UpdateObjectStorageActionResult(result=storage_data)

    async def delete(self, action: DeleteObjectStorageAction) -> DeleteObjectStorageActionResult:
        """
        Delete an existing object storage.
        """
        log.info("Deleting object storage with id: {}", action.storage_id)
        storage_data = await self._object_storage_repository.delete(action.storage_id)
        return DeleteObjectStorageActionResult(deleted_storage_id=storage_data)

    async def get(self, action: GetObjectStorageAction) -> GetObjectStorageActionResult:
        """
        Get an existing object storage by ID.
        """
        log.info("Getting object storage with id: {}", action.storage_id)
        storage_data = await self._object_storage_repository.get_by_id(action.storage_id)
        return GetObjectStorageActionResult(result=storage_data)

    # TODO: Add filtering logic
    async def list(self, action: ListObjectStorageAction) -> ListObjectStorageActionResult:
        """
        List all object storages.
        """
        log.info("Listing object storages")
        storage_data_list = await self._object_storage_repository.list()
        return ListObjectStorageActionResult(data=storage_data_list)
