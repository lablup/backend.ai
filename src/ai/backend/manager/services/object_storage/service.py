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
