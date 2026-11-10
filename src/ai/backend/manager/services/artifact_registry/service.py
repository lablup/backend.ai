import logging
<<<<<<< HEAD

from ai.backend.logging.utils import BraceStyleAdapter
=======
from collections.abc import Mapping, Sequence
from dataclasses import replace

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.data.huggingface_registry.types import (
    HuggingFaceRegistryConnectionData,
    HuggingFaceRegistryData,
)
from ai.backend.manager.data.reservoir_registry.types import (
    ReservoirRegistryConnectionData,
    ReservoirRegistryData,
)
from ai.backend.manager.defs import SECRET_KEY_PLACEHOLDER, TOKEN_PLACEHOLDER
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.specs.types import BulkResultWithFailures
>>>>>>> ca95a63b (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.actions.common.get_meta import (
    GetArtifactRegistryMetaAction,
    GetArtifactRegistryMetaActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.common.search import (
    SearchArtifactRegistriesAction,
    SearchArtifactRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.bulk_get import (
    BulkGetHuggingFaceRegistriesAction,
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
from ai.backend.manager.services.artifact_registry.actions.huggingface.search import (
    SearchHuggingFaceRegistriesAction,
    SearchHuggingFaceRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
    UpdateHuggingFaceRegistryActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.bulk_get import (
    BulkGetReservoirRegistriesAction,
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
from ai.backend.manager.services.artifact_registry.actions.reservoir.search import (
    SearchReservoirRegistriesAction,
    SearchReservoirRegistriesActionResult,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
    UpdateReservoirRegistryActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
        log.info("Creating huggingface registry with data: {}", action.creator)
        registry_data = await self._huggingface_registry_repository.create(
            action.creator, action.meta
        )
        return CreateHuggingFaceRegistryActionResult(
            result=self._with_token_masked_unless_superadmin(registry_data)
        )

    async def update_huggingface_registry(
        self, action: UpdateHuggingFaceRegistryAction
    ) -> UpdateHuggingFaceRegistryActionResult:
        """
        Update an existing huggingface registry.
        """
        log.info("Updating huggingface registry with id: {}", action.updater.registry_id)
        registry_data = await self._huggingface_registry_repository.update(
            action.updater, action.meta
        )
        return UpdateHuggingFaceRegistryActionResult(
            result=self._with_token_masked_unless_superadmin(registry_data)
        )

    async def delete_huggingface_registry(
        self, action: DeleteHuggingFaceRegistryAction
    ) -> DeleteHuggingFaceRegistryActionResult:
        """
        Delete an existing huggingface registry.
        """
        log.info("Deleting huggingface registry with id: {}", action.registry_id)
        registry_data = await self._huggingface_registry_repository.delete(action.registry_id)
        return DeleteHuggingFaceRegistryActionResult(deleted_registry_id=registry_data)

<<<<<<< HEAD
=======
    async def partial_bulk_update_huggingface_registries(
        self, action: PartialBulkUpdateHuggingFaceRegistriesAction
    ) -> PartialBulkResult[HuggingFaceRegistryData]:
        """Edit each named huggingface registry, answering for every one."""
        result = await self._huggingface_registry_repository.partial_bulk_update([
            (item.updater, item.meta) for item in action.items
        ])
        return self._to_partial_bulk_result(
            action.entity_ids(),
            BulkResultWithFailures(
                successes={
                    entity_id: self._with_token_masked_unless_superadmin(registry_data)
                    for entity_id, registry_data in result.successes.items()
                },
                errors=result.errors,
            ),
        )

    async def partial_bulk_purge_huggingface_registries(
        self, action: PartialBulkPurgeHuggingFaceRegistriesAction
    ) -> PartialBulkResult[ArtifactRegistryID]:
        """Remove each named huggingface registry, answering for every one."""
        result = await self._huggingface_registry_repository.partial_bulk_purge(action.ids)
        return self._to_partial_bulk_result(action.entity_ids(), result)

>>>>>>> ca95a63b (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))
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
        return GetHuggingFaceRegistryActionResult(
            result=self._with_token_masked_unless_superadmin(registry_data)
        )

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
        return GetHuggingFaceRegistriesActionResult(
            result=[
                self._with_token_masked_unless_superadmin(registry_data)
                for registry_data in registry_data_list
            ]
        )

    async def bulk_get_huggingface_registries(
        self, action: BulkGetHuggingFaceRegistriesAction
    ) -> PartialBulkResult[HuggingFaceRegistryConnectionData]:
        """Read each named huggingface registry, answering for every one."""
        connections_by_id = await self._huggingface_registry_repository.registry_connections(
            action.ids
        )
        return self._to_partial_bulk_get_result(
            action.entity_ids(),
            {
                entity_id: self._with_token_masked_unless_superadmin(connection)
                for entity_id, connection in connections_by_id.items()
            },
        )

    async def list_huggingface_registry(
        self, _action: ListHuggingFaceRegistryAction
    ) -> ListHuggingFaceRegistryActionResult:
        """
        List all huggingface registries.
        """
        log.info("Listing huggingface registries")
        registry_data_list = await self._huggingface_registry_repository.list_registries()
        return ListHuggingFaceRegistryActionResult(
            data=[
                self._with_token_masked_unless_superadmin(registry_data)
                for registry_data in registry_data_list
            ]
        )

    async def search_huggingface_registries(
        self, action: SearchHuggingFaceRegistriesAction
    ) -> SearchHuggingFaceRegistriesActionResult:
        """Searches HuggingFace registries."""
        result = await self._huggingface_registry_repository.search_registries(
            searcher=action.searcher,
        )

        return SearchHuggingFaceRegistriesActionResult(
            registries=[
                self._with_token_masked_unless_superadmin(registry_data)
                for registry_data in result.items
            ],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create_reservoir_registry(
        self, action: CreateReservoirRegistryAction
    ) -> CreateReservoirActionResult:
        """
        Create a new reservoir.
        """
        log.info("Creating reservoir with data: {}", action.creator)
        reservoir_data = await self._reservoir_repository.create(action.creator, action.meta)
        return CreateReservoirActionResult(
            result=self._with_secret_key_masked_unless_superadmin(reservoir_data)
        )

    async def update_reservoir_registry(
        self, action: UpdateReservoirRegistryAction
    ) -> UpdateReservoirRegistryActionResult:
        """
        Update an existing reservoir.
        """
        log.info("Updating reservoir with id: {}", action.updater.registry_id)
        reservoir_data = await self._reservoir_repository.update(action.updater, action.meta)
        return UpdateReservoirRegistryActionResult(
            result=self._with_secret_key_masked_unless_superadmin(reservoir_data)
        )

    async def delete_reservoir_registry(
        self, action: DeleteReservoirRegistryAction
    ) -> DeleteReservoirActionResult:
        """
        Delete an existing reservoir.
        """
        log.info("Deleting reservoir with id: {}", action.registry_id)
        reservoir_data = await self._reservoir_repository.delete(action.registry_id)
        return DeleteReservoirActionResult(deleted_reservoir_id=reservoir_data)

<<<<<<< HEAD
=======
    async def partial_bulk_update_reservoir_registries(
        self, action: PartialBulkUpdateReservoirRegistriesAction
    ) -> PartialBulkResult[ReservoirRegistryData]:
        """Edit each named reservoir registry, answering for every one."""
        result = await self._reservoir_repository.partial_bulk_update([
            (item.updater, item.meta) for item in action.items
        ])
        return self._to_partial_bulk_result(
            action.entity_ids(),
            BulkResultWithFailures(
                successes={
                    entity_id: self._with_secret_key_masked_unless_superadmin(reservoir_data)
                    for entity_id, reservoir_data in result.successes.items()
                },
                errors=result.errors,
            ),
        )

    async def partial_bulk_purge_reservoir_registries(
        self, action: PartialBulkPurgeReservoirRegistriesAction
    ) -> PartialBulkResult[ArtifactRegistryID]:
        """Remove each named reservoir registry, answering for every one."""
        result = await self._reservoir_repository.partial_bulk_purge(action.ids)
        return self._to_partial_bulk_result(action.entity_ids(), result)

>>>>>>> ca95a63b (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))
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
        return GetReservoirRegistryActionResult(
            result=self._with_secret_key_masked_unless_superadmin(reservoir_data)
        )

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
        return GetReservoirRegistriesActionResult(
            result=[
                self._with_secret_key_masked_unless_superadmin(reservoir_data)
                for reservoir_data in reservoir_data_list
            ]
        )

    async def bulk_get_reservoir_registries(
        self, action: BulkGetReservoirRegistriesAction
    ) -> PartialBulkResult[ReservoirRegistryConnectionData]:
        """Read each named reservoir registry, answering for every one."""
        connections_by_id = await self._reservoir_repository.registry_connections(action.ids)
        return self._to_partial_bulk_get_result(
            action.entity_ids(),
            {
                entity_id: self._with_secret_key_masked_unless_superadmin(connection)
                for entity_id, connection in connections_by_id.items()
            },
        )

    async def list_reservoir_registries(
        self, _action: ListReservoirRegistriesAction
    ) -> ListReservoirRegistriesActionResult:
        """
        List all reservoirs.
        """
        log.info("Listing reservoirs")
        reservoir_data_list = await self._reservoir_repository.list_reservoir_registries()
        return ListReservoirRegistriesActionResult(
            data=[
                self._with_secret_key_masked_unless_superadmin(reservoir_data)
                for reservoir_data in reservoir_data_list
            ]
        )

    async def search_reservoir_registries(
        self, action: SearchReservoirRegistriesAction
    ) -> SearchReservoirRegistriesActionResult:
        """Searches Reservoir registries."""
        result = await self._reservoir_repository.search_registries(
            searcher=action.searcher,
        )
        return SearchReservoirRegistriesActionResult(
            registries=[
                self._with_secret_key_masked_unless_superadmin(reservoir_data)
                for reservoir_data in result.items
            ],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get_registry_meta(
        self, action: GetArtifactRegistryMetaAction
    ) -> GetArtifactRegistryMetaActionResult:
        log.info("Getting artifact registry meta with id: {}", action.registry_id)
        registry_meta = await self._artifact_registry_repository.get_artifact_registry_data(
            action.registry_id
        )
        return GetArtifactRegistryMetaActionResult(result=registry_meta)

    async def search_artifact_registries(
        self, action: SearchArtifactRegistriesAction
    ) -> SearchArtifactRegistriesActionResult:
        """Searches artifact registries."""
        result = await self._artifact_registry_repository.search_artifact_registries(
            searcher=action.searcher,
        )

        return SearchArtifactRegistriesActionResult(
            registries=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
<<<<<<< HEAD
=======

    def _to_partial_bulk_result[TData](
        self, entity_ids: Sequence[EntityIdentifier], result: BulkResultWithFailures[TData]
    ) -> PartialBulkResult[TData]:
        return PartialBulkResult(
            items=[
                PartialBulkEntityResult[TData].succeeded(entity_id, result.successes[entity_id])
                if entity_id in result.successes
                else PartialBulkEntityResult[TData].failed(entity_id, result.errors[entity_id])
                for entity_id in entity_ids
            ]
        )

    def _to_partial_bulk_get_result[TData](
        self, entity_ids: Sequence[EntityIdentifier], data_by_id: Mapping[EntityIdentifier, TData]
    ) -> PartialBulkResult[TData]:
        return PartialBulkResult(
            items=[
                PartialBulkEntityResult[TData].succeeded(entity_id, data_by_id[entity_id])
                if entity_id in data_by_id
                else PartialBulkEntityResult[TData].failed(
                    entity_id,
                    EntityNotFoundError(
                        entity_type=entity_id.entity_type(),
                        operation=ActionOperationType.GET,
                        extra_msg=f"Artifact registry {entity_id} not found",
                    ),
                )
                for entity_id in entity_ids
            ]
        )

    @staticmethod
    def _with_secret_key_masked_unless_superadmin[
        TReservoirData: (ReservoirRegistryData, ReservoirRegistryConnectionData)
    ](reservoir_data: TReservoirData) -> TReservoirData:
        user = current_user()
        return (
            reservoir_data
            if user is not None and user.is_superadmin
            else replace(reservoir_data, secret_key=SECRET_KEY_PLACEHOLDER)
        )

    @staticmethod
    def _with_token_masked_unless_superadmin[
        THuggingFaceData: (HuggingFaceRegistryData, HuggingFaceRegistryConnectionData)
    ](registry_data: THuggingFaceData) -> THuggingFaceData:
        if registry_data.token is None:
            return registry_data
        user = current_user()
        return (
            registry_data
            if user is not None and user.is_superadmin
            else replace(registry_data, token=TOKEN_PLACEHOLDER)
        )
>>>>>>> ca95a63b (fix(BA-8972): mask artifact registry credentials for callers who are not superadmins (#16643))
