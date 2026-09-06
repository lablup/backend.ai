"""V2 SDK client for the entity type registry."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.entity.response import ListEntityTypesPayload

_PATH = "/v2/entity-types"


class V2EntityTypeClient(BaseDomainClient):
    """SDK client for ``/v2/entity-types`` endpoints."""

    async def list(self) -> ListEntityTypesPayload:
        """List every entity type a request may name."""
        return await self._client.typed_request(
            "GET",
            _PATH,
            response_model=ListEntityTypesPayload,
        )
