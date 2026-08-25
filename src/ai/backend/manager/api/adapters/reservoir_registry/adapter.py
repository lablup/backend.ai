"""Reservoir Registry adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
    CreateReservoirRegistryInput,
    DeleteReservoirRegistryInput,
    UpdateReservoirRegistryInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    AdminSearchReservoirRegistriesPayload,
    CreateReservoirRegistryPayload,
    DeleteReservoirRegistryPayload,
    ReservoirRegistryNode,
    UpdateReservoirRegistryPayload,
)
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.reservoir_registry.conditions import ReservoirRegistryConditions
from ai.backend.manager.models.reservoir_registry.creators import ReservoirRegistryCreator
from ai.backend.manager.models.reservoir_registry.searchers import ReservoirRegistrySearcher
from ai.backend.manager.models.reservoir_registry.updaters import ReservoirRegistryUpdater
from ai.backend.manager.models.specs.pagination import OffsetPagination
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
from ai.backend.manager.services.artifact_registry.actions.reservoir.search import (
    SearchReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.update import (
    UpdateReservoirRegistryAction,
)
from ai.backend.manager.types import OptionalState

DEFAULT_PAGINATION_LIMIT = 10


class ReservoirRegistryAdapter(BaseAdapter):
    """Adapter for Reservoir registry domain operations."""

    async def create(self, input: CreateReservoirRegistryInput) -> CreateReservoirRegistryPayload:
        """Create a new Reservoir registry."""
        action_result = await self._processors.artifact_registry.create_reservoir_registry.run(
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
        action_result = await self._processors.artifact_registry.search_reservoir_registries.run(
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
        action_result = await self._processors.artifact_registry.get_reservoir_registry.run(
            GetReservoirRegistryAction(
                registry_id=ArtifactRegistryID(registry_id), reservoir_id=registry_id
            )
        )
        return self._reservoir_registry_data_to_dto(action_result.result)

    async def update(self, input: UpdateReservoirRegistryInput) -> UpdateReservoirRegistryPayload:
        """Update an existing Reservoir registry."""
        updater = ReservoirRegistryUpdater(
            registry_id=ArtifactRegistryID(input.id),
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
        )
        meta = ArtifactRegistryModifierMeta(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
        )
        action_result = await self._processors.artifact_registry.update_reservoir_registry.run(
            UpdateReservoirRegistryAction(
                registry_id=ArtifactRegistryID(input.id),
                updater=updater,
                meta=meta,
            )
        )
        return UpdateReservoirRegistryPayload(
            reservoir=self._reservoir_registry_data_to_dto(action_result.result)
        )

    async def get_many(self, registry_ids: list[UUID]) -> list[ReservoirRegistryNode]:
        """Retrieve multiple Reservoir registries by IDs."""
        action_result = await self._processors.artifact_registry.get_reservoir_registries.run(
            GetReservoirRegistriesAction(registry_ids=registry_ids)
        )
        return [self._reservoir_registry_data_to_dto(item) for item in action_result.result]

    async def batch_load_by_ids(self, ids: Sequence[UUID]) -> list[ReservoirRegistryNode | None]:
        """Batch load Reservoir registries by IDs for DataLoader use.

        Returns ReservoirRegistryNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        searcher = ReservoirRegistrySearcher(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[ReservoirRegistryConditions.by_ids(ids)],
        )
        action_result = await self._processors.artifact_registry.search_reservoir_registries.run(
            SearchReservoirRegistriesAction(searcher=searcher)
        )
        registry_map = {
            item.id: self._reservoir_registry_data_to_dto(item) for item in action_result.registries
        }
        return [registry_map.get(registry_id) for registry_id in ids]

    async def delete(self, input: DeleteReservoirRegistryInput) -> DeleteReservoirRegistryPayload:
        """Delete a Reservoir registry."""
        action_result = await self._processors.artifact_registry.delete_reservoir_registry.run(
            DeleteReservoirRegistryAction(registry_id=ArtifactRegistryID(input.id))
        )
        return DeleteReservoirRegistryPayload(id=action_result.deleted_reservoir_id)

    @staticmethod
    def _reservoir_registry_data_to_dto(data: ReservoirRegistryData) -> ReservoirRegistryNode:
        return ReservoirRegistryNode(
            id=data.id,
            name=data.name,
            endpoint=data.endpoint,
            access_key=data.access_key,
            secret_key=data.secret_key,
            api_version=data.api_version,
        )
