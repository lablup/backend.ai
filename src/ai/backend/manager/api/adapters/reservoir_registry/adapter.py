"""Reservoir Registry adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.dto.manager.v2.common import PartialBulkFailure, PartialBulkPayload
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
    CreateReservoirRegistryInput,
    PartialBulkPurgeReservoirRegistriesInput,
    PartialBulkUpdateReservoirRegistriesInput,
    UpdateReservoirRegistryBody,
    UpdateReservoirRegistryInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    AdminSearchReservoirRegistriesPayload,
    CreateReservoirRegistryPayload,
    PurgeReservoirRegistryPayload,
    ReservoirRegistryNode,
    UpdateReservoirRegistryPayload,
)
from ai.backend.manager.actions.v2.bulk.result import PartialBulkResult
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryData,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.reservoir_registry.types import (
    ReservoirRegistryConnectionData,
    ReservoirRegistryData,
)
from ai.backend.manager.models.reservoir_registry.creators import ReservoirRegistryCreator
from ai.backend.manager.models.reservoir_registry.searchers import ReservoirRegistrySearcher
from ai.backend.manager.models.reservoir_registry.updaters import ReservoirRegistryUpdater
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.services.artifact_registry.actions.common.get_multi import (
    GetArtifactRegistryMetasAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.bulk_get import (
    BulkGetReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.create import (
    CreateReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.delete import (
    DeleteReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get import (
    GetReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get_multi import (
    GetReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.partial_bulk_purge import (
    PartialBulkPurgeReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.partial_bulk_update import (
    PartialBulkUpdateReservoirRegistriesAction,
    PartialBulkUpdateReservoirRegistryItem,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.search import (
    SearchReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.processors import ArtifactRegistryProcessors
from ai.backend.manager.types import OptionalState

DEFAULT_PAGINATION_LIMIT = 10


class ReservoirRegistryAdapter(BaseAdapter):
    """Adapter for Reservoir registry domain operations."""

    _artifact_registry: ArtifactRegistryProcessors

    def __init__(self, artifact_registry: ArtifactRegistryProcessors) -> None:
        self._artifact_registry = artifact_registry

    async def create(self, input: CreateReservoirRegistryInput) -> CreateReservoirRegistryPayload:
        """Create a new Reservoir registry."""
        action_result = await self._artifact_registry.create_reservoir_registry.run(
            CreateReservoirRegistryAction(
                creator=ReservoirRegistryCreator(
                    endpoint=input.endpoint,
                    access_key=input.access_key,
                    secret_key=input.secret_key,
                    api_version=input.api_version,
                ),
                meta=ArtifactRegistryCreatorMeta(name=input.name),
            )
        )
        return CreateReservoirRegistryPayload(
            reservoir=self._reservoir_registry_data_to_dto(action_result.result)
        )

    async def search(
        self, input: AdminSearchReservoirRegistriesInput
    ) -> AdminSearchReservoirRegistriesPayload:
        """Search Reservoir registries with pagination."""
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        searcher = ReservoirRegistrySearcher(pagination=pagination, conditions=[], orders=[])
        action_result = await self._artifact_registry.search_reservoir_registries.run(
            SearchReservoirRegistriesAction(searcher=searcher)
        )
        return AdminSearchReservoirRegistriesPayload(
            items=[self._reservoir_registry_data_to_dto(item) for item in action_result.registries],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, registry_id: UUID) -> ReservoirRegistryNode:
        """Retrieve a single Reservoir registry by ID."""
        action_result = await self._artifact_registry.get_reservoir_registry.run(
            GetReservoirRegistryAction(
                registry_id=ArtifactRegistryID(registry_id), reservoir_id=registry_id
            )
        )
        return self._reservoir_registry_data_to_dto(action_result.result)

    async def update(self, input: UpdateReservoirRegistryInput) -> UpdateReservoirRegistryPayload:
        """Update an existing Reservoir registry."""
        registry_id = ArtifactRegistryID(input.id)
        item = self._to_update_item(registry_id, input)
        action_result = await self._artifact_registry.update_reservoir_registry.run(
            UpdateReservoirRegistryAction(
                registry_id=registry_id,
                updater=item.updater,
                meta=item.meta,
            )
        )
        return UpdateReservoirRegistryPayload(
            reservoir=self._reservoir_registry_data_to_dto(action_result.result)
        )

    async def partial_bulk_update(
        self, input: PartialBulkUpdateReservoirRegistriesInput
    ) -> PartialBulkPayload[ReservoirRegistryNode]:
        """Update several Reservoir registries, answering for each one."""
        result = await self._artifact_registry.partial_bulk_update_reservoir_registries.run(
            PartialBulkUpdateReservoirRegistriesAction(
                items=[
                    self._to_update_item(ArtifactRegistryID(item.id), item.input)
                    for item in input.items
                ]
            )
        )
        return PartialBulkPayload[ReservoirRegistryNode](
            successes=[
                self._reservoir_registry_data_to_dto(item.value)
                for item in result.items
                if item.value is not None
            ],
            failed=self._to_failures(result),
        )

    def _to_update_item(
        self, registry_id: ArtifactRegistryID, input: UpdateReservoirRegistryBody
    ) -> PartialBulkUpdateReservoirRegistryItem:
        return PartialBulkUpdateReservoirRegistryItem(
            updater=ReservoirRegistryUpdater(
                registry_id=registry_id,
                endpoint=(
                    OptionalState.update(input.endpoint)
                    if input.endpoint is not None
                    else OptionalState.nop()
                ),
                access_key=(
                    OptionalState.update(input.access_key)
                    if input.access_key is not None
                    else OptionalState.nop()
                ),
                secret_key=(
                    OptionalState.update(input.secret_key)
                    if input.secret_key is not None
                    else OptionalState.nop()
                ),
                api_version=(
                    OptionalState.update(input.api_version)
                    if input.api_version is not None
                    else OptionalState.nop()
                ),
            ),
            meta=ArtifactRegistryModifierMeta(
                name=(
                    OptionalState.update(input.name)
                    if input.name is not None
                    else OptionalState.nop()
                ),
            ),
        )

    async def get_many(self, registry_ids: list[UUID]) -> list[ReservoirRegistryNode]:
        """Retrieve multiple Reservoir registries by IDs."""
        action_result = await self._artifact_registry.get_reservoir_registries.run(
            GetReservoirRegistriesAction(registry_ids=registry_ids)
        )
        return [self._reservoir_registry_data_to_dto(item) for item in action_result.result]

    async def batch_load_by_ids(
        self, ids: Sequence[UUID]
    ) -> list[ReservoirRegistryNode | Exception | None]:
        """Batch load Reservoir registries by IDs for DataLoader use, checked per registry.

        The name is read from the artifact registry row, for the registries that were read.
        """
        if not ids:
            return []
        result = await self._artifact_registry.bulk_get_reservoir_registries.run(
            BulkGetReservoirRegistriesAction(
                ids=[ArtifactRegistryID(registry_id) for registry_id in ids]
            )
        )
        metas = (
            await self._artifact_registry.get_registry_metas.run(
                GetArtifactRegistryMetasAction(
                    registry_ids=[ArtifactRegistryID(entity_id) for entity_id in result.values()]
                )
            )
        ).values()
        return [
            self._connection_to_dto(item.value, metas[item.entity_id])
            if item.value is not None and item.entity_id in metas
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    def _connection_to_dto(
        self, connection: ReservoirRegistryConnectionData, meta: ArtifactRegistryData
    ) -> ReservoirRegistryNode:
        return ReservoirRegistryNode(
            id=connection.id,
            entity_id=connection.entity_id(),
            name=meta.name,
            endpoint=connection.endpoint,
            access_key=connection.access_key,
            secret_key=connection.secret_key,
            api_version=connection.api_version,
        )

    async def purge(self, registry_id: UUID) -> PurgeReservoirRegistryPayload:
        """Permanently delete a Reservoir registry."""
        action_result = await self._artifact_registry.delete_reservoir_registry.run(
            DeleteReservoirRegistryAction(registry_id=ArtifactRegistryID(registry_id))
        )
        return PurgeReservoirRegistryPayload(id=action_result.deleted_reservoir_id)

    async def partial_bulk_purge(
        self, input: PartialBulkPurgeReservoirRegistriesInput
    ) -> PartialBulkPayload[PurgeReservoirRegistryPayload]:
        """Permanently delete several Reservoir registries, answering for each one."""
        result = await self._artifact_registry.partial_bulk_purge_reservoir_registries.run(
            PartialBulkPurgeReservoirRegistriesAction(
                ids=[ArtifactRegistryID(registry_id) for registry_id in input.ids]
            )
        )
        return PartialBulkPayload[PurgeReservoirRegistryPayload](
            successes=[
                PurgeReservoirRegistryPayload(id=item.value)
                for item in result.items
                if item.value is not None
            ],
            failed=self._to_failures(result),
        )

    def _to_failures(self, result: PartialBulkResult[Any]) -> list[PartialBulkFailure]:
        return [
            PartialBulkFailure(id=item.entity_id, message=str(item.error))
            for item in result.items
            if item.error is not None
        ]

    @staticmethod
    def _reservoir_registry_data_to_dto(data: ReservoirRegistryData) -> ReservoirRegistryNode:
        return ReservoirRegistryNode(
            id=data.id,
            entity_id=data.id,
            name=data.name,
            endpoint=data.endpoint,
            access_key=data.access_key,
            secret_key=data.secret_key,
            api_version=data.api_version,
        )
