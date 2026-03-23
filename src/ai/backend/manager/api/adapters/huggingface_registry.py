"""HuggingFace Registry adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    AdminSearchHuggingFaceRegistriesInput,
    CreateHuggingFaceRegistryInput,
    DeleteHuggingFaceRegistryInput,
    UpdateHuggingFaceRegistryInput,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    AdminSearchHuggingFaceRegistriesPayload,
    CreateHuggingFaceRegistryPayload,
    DeleteHuggingFaceRegistryPayload,
    HuggingFaceRegistryNode,
    UpdateHuggingFaceRegistryPayload,
)
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryCreatorMeta,
    ArtifactRegistryModifierMeta,
)
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry.conditions import HuggingFaceRegistryConditions
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination, Updater
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.huggingface_registry import HuggingFaceRegistryCreatorSpec
from ai.backend.manager.repositories.huggingface_registry.updaters import (
    HuggingFaceRegistryUpdaterSpec,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.create import (
    CreateHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.delete import (
    DeleteHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get import (
    GetHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get_multi import (
    GetHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.search import (
    SearchHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.update import (
    UpdateHuggingFaceRegistryAction,
)
from ai.backend.manager.types import OptionalState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class HuggingFaceRegistryAdapter(BaseAdapter):
    """Adapter for HuggingFace registry domain operations."""

    async def create(
        self, input: CreateHuggingFaceRegistryInput
    ) -> CreateHuggingFaceRegistryPayload:
        """Create a new HuggingFace registry."""
        action_result = (
            await self._processors.artifact_registry.create_huggingface_registry.wait_for_complete(
                CreateHuggingFaceRegistryAction(
                    creator=Creator(
                        spec=HuggingFaceRegistryCreatorSpec(
                            url=input.url,
                            token=input.token,
                        )
                    ),
                    meta=ArtifactRegistryCreatorMeta(name=input.name),
                )
            )
        )
        return CreateHuggingFaceRegistryPayload(
            huggingface_registry=self._huggingface_registry_data_to_dto(action_result.result)
        )

    async def search(
        self, input: AdminSearchHuggingFaceRegistriesInput
    ) -> AdminSearchHuggingFaceRegistriesPayload:
        """Search HuggingFace registries with pagination."""
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        querier = BatchQuerier(conditions=[], orders=[], pagination=pagination)
        action_result = await self._processors.artifact_registry.search_huggingface_registries.wait_for_complete(
            SearchHuggingFaceRegistriesAction(querier=querier)
        )
        return AdminSearchHuggingFaceRegistriesPayload(
            items=[
                self._huggingface_registry_data_to_dto(item) for item in action_result.registries
            ],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, registry_id: UUID) -> HuggingFaceRegistryNode:
        """Retrieve a single HuggingFace registry by ID."""
        action_result = (
            await self._processors.artifact_registry.get_huggingface_registry.wait_for_complete(
                GetHuggingFaceRegistryAction(registry_id=registry_id)
            )
        )
        return self._huggingface_registry_data_to_dto(action_result.result)

    async def update(
        self, input: UpdateHuggingFaceRegistryInput
    ) -> UpdateHuggingFaceRegistryPayload:
        """Update an existing HuggingFace registry."""
        spec = HuggingFaceRegistryUpdaterSpec(
            url=OptionalState.update(input.url) if input.url is not None else OptionalState.nop(),
            token=(
                OptionalState.update(input.token)
                if input.token is not None
                else OptionalState.nop()
            ),
        )
        meta = ArtifactRegistryModifierMeta(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
        )
        action_result = (
            await self._processors.artifact_registry.update_huggingface_registry.wait_for_complete(
                UpdateHuggingFaceRegistryAction(
                    updater=Updater(spec=spec, pk_value=input.id),
                    meta=meta,
                )
            )
        )
        return UpdateHuggingFaceRegistryPayload(
            huggingface_registry=self._huggingface_registry_data_to_dto(action_result.result)
        )

    async def get_many(self, registry_ids: list[UUID]) -> list[HuggingFaceRegistryNode]:
        """Retrieve multiple HuggingFace registries by IDs."""
        action_result = (
            await self._processors.artifact_registry.get_huggingface_registries.wait_for_complete(
                GetHuggingFaceRegistriesAction(registry_ids=registry_ids)
            )
        )
        return [self._huggingface_registry_data_to_dto(item) for item in action_result.result]

    async def batch_load_by_ids(self, ids: Sequence[UUID]) -> list[HuggingFaceRegistryNode | None]:
        """Batch load HuggingFace registries by IDs for DataLoader use.

        Returns HuggingFaceRegistryNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[HuggingFaceRegistryConditions.by_ids(ids)],
        )
        action_result = await self._processors.artifact_registry.search_huggingface_registries.wait_for_complete(
            SearchHuggingFaceRegistriesAction(querier=querier)
        )
        registry_map = {
            item.id: self._huggingface_registry_data_to_dto(item)
            for item in action_result.registries
        }
        return [registry_map.get(registry_id) for registry_id in ids]

    async def delete(
        self, input: DeleteHuggingFaceRegistryInput
    ) -> DeleteHuggingFaceRegistryPayload:
        """Delete a HuggingFace registry."""
        action_result = (
            await self._processors.artifact_registry.delete_huggingface_registry.wait_for_complete(
                DeleteHuggingFaceRegistryAction(registry_id=input.id)
            )
        )
        return DeleteHuggingFaceRegistryPayload(id=action_result.deleted_registry_id)

    @staticmethod
    def _huggingface_registry_data_to_dto(
        data: HuggingFaceRegistryData,
    ) -> HuggingFaceRegistryNode:
        return HuggingFaceRegistryNode(
            id=data.id,
            name=data.name,
            url=data.url,
            token=data.token,
        )
