"""V2 SDK client for the label domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.entity_label.request import (
    PartialBulkPurgeEntityLabelInput,
    PartialBulkUpsertEntityLabelInput,
    SearchEntityLabelsInput,
    UpsertEntityLabelInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
    PartialBulkPurgeEntityLabelPayload,
    PartialBulkUpsertEntityLabelPayload,
    PurgeEntityLabelPayload,
    SearchEntityLabelsPayload,
    UpsertEntityLabelPayload,
)

_PATH = "/v2/entity-labels"


class V2EntityLabelClient(BaseDomainClient):
    """SDK client for label operations."""

    async def upsert(self, request: UpsertEntityLabelInput) -> UpsertEntityLabelPayload:
        """Set one key on an entity, replacing the value it carries."""
        return await self._client.typed_request(
            "PUT",
            _PATH,
            request=request,
            response_model=UpsertEntityLabelPayload,
        )

    async def partial_bulk_upsert(
        self, request: PartialBulkUpsertEntityLabelInput
    ) -> PartialBulkUpsertEntityLabelPayload:
        """Set keys on several entities in one call, answering per entity."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-upsert",
            request=request,
            response_model=PartialBulkUpsertEntityLabelPayload,
        )

    async def purge(self, label_id: UUID) -> PurgeEntityLabelPayload:
        """Take one label off, named by its own id."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{label_id}",
            response_model=PurgeEntityLabelPayload,
        )

    async def partial_bulk_purge(
        self, request: PartialBulkPurgeEntityLabelInput
    ) -> PartialBulkPurgeEntityLabelPayload:
        """Take several labels off in one call, answering per label."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPurgeEntityLabelPayload,
        )

    async def search(self, request: SearchEntityLabelsInput) -> SearchEntityLabelsPayload:
        """Read the labels on the entities named."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchEntityLabelsPayload,
        )
