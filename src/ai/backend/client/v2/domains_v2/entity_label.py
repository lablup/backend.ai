"""V2 SDK client for the label domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.entity_label.request import (
    SearchEntityLabelsInput,
    UpsertEntityLabelInput,
)
from ai.backend.common.dto.manager.v2.entity_label.response import (
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

    async def purge(self, label_id: UUID) -> PurgeEntityLabelPayload:
        """Take one label off, named by its own id."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{label_id}",
            response_model=PurgeEntityLabelPayload,
        )

    async def search(self, request: SearchEntityLabelsInput) -> SearchEntityLabelsPayload:
        """Read the labels on the entities named."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchEntityLabelsPayload,
        )
