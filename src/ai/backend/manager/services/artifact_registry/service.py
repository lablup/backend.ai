import logging

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
    GetArtifactRegistryMetaActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
    GetArtifactRegistryMetasActionResult,
)
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
from ai.backend.manager.services.artifact_registry.actions.huggingface.get_multi import (
    GetHuggingFaceRegistriesAction,
    GetHuggingFaceRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.list import (
    ListHuggingFaceRegistryAction,
    ListHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
    UpdateHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.create import (
    CreateReservoirActionResult,
    CreateReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.delete import (
    DeleteReservoirActionResult,
    DeleteReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get import (
    GetReservoirRegistryAction,
    GetReservoirRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get_multi import (
    GetReservoirRegistriesAction,
    GetReservoirRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.list import (
    ListReservoirRegistriesAction,
    ListReservoirRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
    UpdateReservoirRegistryActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class ArtifactRegistryService:
    _huggingface_registry_repository: HuggingFaceRepository
    _reservoir_repository: ReservoirRegistryRepository
    _artifact_registry_repository: ArtifactRegistryRepository

    def __init__(
        self,
        huggingface_registry_repository: HuggingFaceRepository,
        reservoir_repository: ReservoirRegistryRepository,
        artifact_registry_repository: ArtifactRegistryRepository,
    ) -> None:
        self._huggingface_registry_repository = huggingface_registry_repository
        self._reservoir_repository = reservoir_repository
        self._artifact_registry_repository = artifact_registry_repository

    async def create_huggingface_registry(
        self, action: CreateHuggingFaceRegistryAction
    ) -> CreateHuggingFaceRegistryActionResult:
        """
        Create a new huggingface registry.
        """
        log.info("Creating huggingface registry with data: {}", action.creator.fields_to_store())
        registry_data = await self._huggingface_registry_repository.create(
            action.creator, action.meta
        )
        return CreateHuggingFaceRegistryActionResult(result=registry_data)

    async def update_huggingface_registry(
        self, action: UpdateHuggingFaceRegistryAction
    ) -> UpdateHuggingFaceRegistryActionResult:
        """
        Update an existing huggingface registry.
        """
        log.info("Updating huggingface registry with data: {}", action.modifier.fields_to_update())
        registry_data = await self._huggingface_registry_repository.update(
            action.id, action.modifier, action.meta
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

    async def get_huggingface_registries(
        self, action: GetHuggingFaceRegistriesAction
    ) -> GetHuggingFaceRegistriesActionResult:
        """
        Get multiple huggingface registries by IDs in a single batch query.
        """
        log.info("Getting {} huggingface registries", len(action.registry_ids))
        registry_data_list = await self._huggingface_registry_repository.get_registries_by_ids(
            action.registry_ids
        )
        return GetHuggingFaceRegistriesActionResult(result=registry_data_list)

    async def list_huggingface_registry(
        self, action: ListHuggingFaceRegistryAction
    ) -> ListHuggingFaceRegistryActionResult:
        """
        List all huggingface registries.
        """
        log.info("Listing huggingface registries")
        registry_data_list = await self._huggingface_registry_repository.list_registries()
        return ListHuggingFaceRegistryActionResult(data=registry_data_list)

    async def create_reservoir_registry(
        self, action: CreateReservoirRegistryAction
    ) -> CreateReservoirActionResult:
        """
        Create a new reservoir.
        """
        log.info("Creating reservoir with data: {}", action.creator.fields_to_store())
        reservoir_data = await self._reservoir_repository.create(action.creator, action.meta)
        return CreateReservoirActionResult(result=reservoir_data)

    async def update_reservoir_registry(
        self, action: UpdateReservoirRegistryAction
    ) -> UpdateReservoirRegistryActionResult:
        """
        Update an existing reservoir.
        """
        log.info("Updating reservoir with data: {}", action.modifier.fields_to_update())
        reservoir_data = await self._reservoir_repository.update(
            action.id, action.modifier, action.meta
        )
        return UpdateReservoirRegistryActionResult(result=reservoir_data)

    async def delete_reservoir_registry(
        self, action: DeleteReservoirRegistryAction
    ) -> DeleteReservoirActionResult:
        """
        Delete an existing reservoir.
        """
        log.info("Deleting reservoir with id: {}", action.reservoir_id)
        reservoir_data = await self._reservoir_repository.delete(action.reservoir_id)
        return DeleteReservoirActionResult(deleted_reservoir_id=reservoir_data)

    async def get_reservoir_registry(
        self, action: GetReservoirRegistryAction
    ) -> GetReservoirRegistryActionResult:
        """
        Get an existing reservoir by ID.
        """
        log.info("Getting reservoir with id: {}", action.reservoir_id)
        reservoir_data = await self._reservoir_repository.get_reservoir_registry_data_by_id(
            action.reservoir_id
        )
        return GetReservoirRegistryActionResult(result=reservoir_data)

    async def get_reservoir_registries(
        self, action: GetReservoirRegistriesAction
    ) -> GetReservoirRegistriesActionResult:
        """
        Get multiple reservoir registries by IDs in a single batch query.
        """
        log.info("Getting {} reservoir registries", len(action.registry_ids))
        reservoir_data_list = await self._reservoir_repository.get_registries_by_ids(
            action.registry_ids
        )
        return GetReservoirRegistriesActionResult(result=reservoir_data_list)

    async def list_reservoir_registries(
        self, action: ListReservoirRegistriesAction
    ) -> ListReservoirRegistriesActionResult:
        """
        List all reservoirs.
        """
        log.info("Listing reservoirs")
        reservoir_data_list = await self._reservoir_repository.list_reservoir_registries()
        return ListReservoirRegistriesActionResult(data=reservoir_data_list)

    async def get_registry_meta(
        self, action: GetArtifactRegistryMetaAction
    ) -> GetArtifactRegistryMetaActionResult:
        log.info("Getting artifact registry meta with id: {}", action.registry_id)
        if action.registry_id:
            registry_meta = await self._artifact_registry_repository.get_artifact_registry_data(
                action.registry_id
            )
        elif action.registry_name:
            registry_meta = (
                await self._artifact_registry_repository.get_artifact_registry_data_by_name(
                    action.registry_name
                )
            )
        else:
            raise InvalidAPIParameters("Either registry_id or registry_name must be provided.")
        return GetArtifactRegistryMetaActionResult(result=registry_meta)

    async def get_registry_metas(
        self, action: GetArtifactRegistryMetasAction
    ) -> GetArtifactRegistryMetasActionResult:
        log.info("Getting {} artifact registry metas", len(action.registry_ids))
        registry_metas = await self._artifact_registry_repository.get_artifact_registry_datas(
            action.registry_ids
        )
        return GetArtifactRegistryMetasActionResult(result=registry_metas)
