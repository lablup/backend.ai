"""Object storage domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

import json
from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
    CreateObjectStorageInput,
    DeleteObjectStorageInput,
    ObjectStorageFilter,
    ObjectStorageOrder,
    UpdateObjectStorageInput,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    AdminSearchObjectStoragesPayload,
    CreateObjectStoragePayload,
    DeleteObjectStoragePayload,
    ObjectStorageNode,
    PresignedDownloadURLPayload,
    PresignedUploadURLPayload,
    UpdateObjectStoragePayload,
)
from ai.backend.common.dto.manager.v2.object_storage.types import OrderDirection
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.conditions import ObjectStorageConditions
from ai.backend.manager.models.object_storage.orders import ObjectStorageOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    Updater,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.object_storage import ObjectStorageCreatorSpec
from ai.backend.manager.repositories.object_storage.updaters import ObjectStorageUpdaterSpec
from ai.backend.manager.services.object_storage.actions.create import CreateObjectStorageAction
from ai.backend.manager.services.object_storage.actions.delete import DeleteObjectStorageAction
from ai.backend.manager.services.object_storage.actions.get import GetObjectStorageAction
from ai.backend.manager.services.object_storage.actions.get_download_presigned_url import (
    GetDownloadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.get_upload_presigned_url import (
    GetUploadPresignedURLAction,
)
from ai.backend.manager.services.object_storage.actions.search import SearchObjectStoragesAction
from ai.backend.manager.services.object_storage.actions.update import UpdateObjectStorageAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 50


class ObjectStorageAdapter(BaseAdapter):
    """Adapter for object storage domain operations."""

    async def admin_search(
        self, input: AdminSearchObjectStoragesInput
    ) -> AdminSearchObjectStoragesPayload:
        """Search object storages with admin scope.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = (
            await self._processors.object_storage.search_object_storages.wait_for_complete(
                SearchObjectStoragesAction(querier=querier)
            )
        )

        return AdminSearchObjectStoragesPayload(
            items=[self._data_to_dto(item) for item in action_result.storages],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchObjectStoragesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: ObjectStorageFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ObjectStorageConditions.by_name_contains,
                equals_factory=ObjectStorageConditions.by_name_equals,
                starts_with_factory=ObjectStorageConditions.by_name_starts_with,
                ends_with_factory=ObjectStorageConditions.by_name_ends_with,
                in_factory=ObjectStorageConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.host is not None:
            condition = self.convert_string_filter(
                filter.host,
                contains_factory=ObjectStorageConditions.by_host_contains,
                equals_factory=ObjectStorageConditions.by_host_equals,
                starts_with_factory=ObjectStorageConditions.by_host_starts_with,
                ends_with_factory=ObjectStorageConditions.by_host_ends_with,
                in_factory=ObjectStorageConditions.by_host_in,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    @staticmethod
    def _convert_orders(orders: list[ObjectStorageOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field.value:
                case "name":
                    result.append(ObjectStorageOrders.name(ascending))
                case "host":
                    result.append(ObjectStorageOrders.host(ascending))
                case "region":
                    result.append(ObjectStorageOrders.region(ascending))
        return result

    @staticmethod
    def _build_pagination(input: AdminSearchObjectStoragesInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    async def batch_load_by_ids(self, ids: Sequence[UUID]) -> list[ObjectStorageNode | None]:
        """Batch load object storages by IDs for DataLoader use.

        Returns ObjectStorageNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[ObjectStorageConditions.by_ids(ids)],
        )
        action_result = (
            await self._processors.object_storage.search_object_storages.wait_for_complete(
                SearchObjectStoragesAction(querier=querier)
            )
        )
        storage_map = {item.id: self._data_to_dto(item) for item in action_result.storages}
        return [storage_map.get(storage_id) for storage_id in ids]

    async def get(self, storage_id: UUID) -> ObjectStorageNode:
        """Retrieve a single object storage by ID."""
        action_result = await self._processors.object_storage.get.wait_for_complete(
            GetObjectStorageAction(storage_id=storage_id)
        )
        return self._data_to_dto(action_result.result)

    async def create(self, input: CreateObjectStorageInput) -> CreateObjectStoragePayload:
        """Create a new object storage."""
        action_result = await self._processors.object_storage.create.wait_for_complete(
            CreateObjectStorageAction(
                creator=Creator(
                    spec=ObjectStorageCreatorSpec(
                        name=input.name,
                        host=input.host,
                        access_key=input.access_key,
                        secret_key=input.secret_key,
                        endpoint=input.endpoint,
                        region=input.region,
                    )
                )
            )
        )
        return CreateObjectStoragePayload(object_storage=self._data_to_dto(action_result.result))

    async def update(self, input: UpdateObjectStorageInput) -> UpdateObjectStoragePayload:
        """Update an existing object storage."""
        spec = ObjectStorageUpdaterSpec(
            name=OptionalState.update(input.name)
            if input.name is not None
            else OptionalState.nop(),
            host=OptionalState.update(input.host)
            if input.host is not None
            else OptionalState.nop(),
            access_key=OptionalState.update(input.access_key)
            if input.access_key is not None
            else OptionalState.nop(),
            secret_key=OptionalState.update(input.secret_key)
            if input.secret_key is not None
            else OptionalState.nop(),
            endpoint=OptionalState.update(input.endpoint)
            if input.endpoint is not None
            else OptionalState.nop(),
            region=(
                TriState.nop()
                if isinstance(input.region, Sentinel)
                else TriState.nullify()
                if input.region is None
                else TriState.update(input.region)
            ),
        )
        action_result = await self._processors.object_storage.update.wait_for_complete(
            UpdateObjectStorageAction(updater=Updater(spec=spec, pk_value=input.id))
        )
        return UpdateObjectStoragePayload(object_storage=self._data_to_dto(action_result.result))

    async def delete(self, input: DeleteObjectStorageInput) -> DeleteObjectStoragePayload:
        """Delete an object storage."""
        action_result = await self._processors.object_storage.delete.wait_for_complete(
            DeleteObjectStorageAction(storage_id=input.id)
        )
        return DeleteObjectStoragePayload(id=action_result.deleted_storage_id)

    async def get_presigned_download_url(
        self,
        artifact_revision_id: UUID,
        key: str,
        expiration: int | None = None,
    ) -> PresignedDownloadURLPayload:
        """Generate a presigned download URL for an artifact revision."""
        action_result = (
            await self._processors.object_storage.get_presigned_download_url.wait_for_complete(
                GetDownloadPresignedURLAction(
                    artifact_revision_id=artifact_revision_id,
                    key=key,
                    expiration=expiration,
                )
            )
        )
        return PresignedDownloadURLPayload(presigned_url=action_result.presigned_url)

    async def get_presigned_upload_url(
        self,
        artifact_revision_id: UUID,
        key: str,
    ) -> PresignedUploadURLPayload:
        """Generate a presigned upload URL for an artifact revision."""
        action_result = (
            await self._processors.object_storage.get_presigned_upload_url.wait_for_complete(
                GetUploadPresignedURLAction(
                    artifact_revision_id=artifact_revision_id,
                    key=key,
                )
            )
        )
        return PresignedUploadURLPayload(
            presigned_url=action_result.presigned_url,
            fields=json.dumps(action_result.fields),
        )

    @staticmethod
    def _data_to_dto(data: ObjectStorageData) -> ObjectStorageNode:
        """Convert data layer type to Pydantic DTO."""
        return ObjectStorageNode(
            id=data.id,
            name=data.name,
            host=data.host,
            access_key=data.access_key,
            secret_key=data.secret_key,
            endpoint=data.endpoint,
            region=data.region,
        )
