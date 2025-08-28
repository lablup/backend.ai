import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.services.artifact_registry.actions.huggingface.create import (
    CreateHuggingFaceRegistryAction,
    CreateHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.delete import (
    DeleteHuggingFaceRegistryAction,
    DeleteHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get import (
    GetHuggingFaceRegistryAction,
    GetHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.list import (
    ListHuggingFaceRegistryAction,
    ListHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
    UpdateHuggingFaceRegistryActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ArtifactRegistryService:
    _huggingface_registry_repository: HuggingFaceRepository

    def __init__(self, huggingface_registry_repository: HuggingFaceRepository) -> None:
        self._huggingface_registry_repository = huggingface_registry_repository

    async def create_huggingface_registry(
        self, action: CreateHuggingFaceRegistryAction
    ) -> CreateHuggingFaceRegistryActionResult:
        """
        Create a new huggingface registry.
        """
        log.info("Creating huggingface registry with data: {}", action.creator.fields_to_store())
        registry_data = await self._huggingface_registry_repository.create(action.creator)
        return CreateHuggingFaceRegistryActionResult(result=registry_data)

    async def update_huggingface_registry(
        self, action: UpdateHuggingFaceRegistryAction
    ) -> UpdateHuggingFaceRegistryActionResult:
        """
        Update an existing huggingface registry.
        """
        log.info("Updating huggingface registry with data: {}", action.modifier.fields_to_update())
        registry_data = await self._huggingface_registry_repository.update(
            action.id, action.modifier
        )
        return UpdateHuggingFaceRegistryActionResult(result=registry_data)

    async def delete_huggingface_registry(
        self, action: DeleteHuggingFaceRegistryAction
    ) -> DeleteHuggingFaceRegistryActionResult:
        """
        Delete an existing huggingface registry.
        """
        log.info("Deleting huggingface registry with id: {}", action.registry_id)
        registry_data = await self._huggingface_registry_repository.delete(action.registry_id)
        return DeleteHuggingFaceRegistryActionResult(deleted_registry_id=registry_data)

    async def get_huggingface_registry(
        self, action: GetHuggingFaceRegistryAction
    ) -> GetHuggingFaceRegistryActionResult:
        """
        Get an existing huggingface registry by ID.
        """
        log.info("Getting huggingface registry with id: {}", action.registry_id)
        registry_data = await self._huggingface_registry_repository.get_registry_data_by_id(
            action.registry_id
        )
        return GetHuggingFaceRegistryActionResult(result=registry_data)

    async def list_huggingface_registry(
        self, action: ListHuggingFaceRegistryAction
    ) -> ListHuggingFaceRegistryActionResult:
        """
        List all huggingface registries.
        """
        log.info("Listing huggingface registries")
        registry_data_list = await self._huggingface_registry_repository.list_registries()
        return ListHuggingFaceRegistryActionResult(data=registry_data_list)
