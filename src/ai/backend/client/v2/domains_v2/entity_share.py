"""V2 SDK client for the entity invitation domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.entity_share.request import (
    CreateEntityShareInput,
    ScopedSearchEntitySharesInput,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntitySharePayload,
    SearchEntitySharesPayload,
)

_PATH = "/v2/entity-shares"


class V2EntityShareClient(BaseDomainClient):
    """SDK client for entity invitation operations."""

    async def create(self, request: CreateEntityShareInput) -> EntitySharePayload:
        """Offer one entity to one address."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=EntitySharePayload,
        )

    async def get(self, share_id: UUID) -> EntitySharePayload:
        """Read one invitation from the side that offered it."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{share_id}",
            response_model=EntitySharePayload,
        )

    async def accept(self, share_id: UUID) -> EntitySharePayload:
        """Take what was offered."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{share_id}/accept",
            response_model=EntitySharePayload,
        )

    async def reject(self, share_id: UUID) -> EntitySharePayload:
        """Turn down what was offered."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{share_id}/reject",
            response_model=EntitySharePayload,
        )

    async def cancel(self, share_id: UUID) -> EntitySharePayload:
        """Withdraw the offer before it was answered."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{share_id}",
            response_model=EntitySharePayload,
        )

    async def scoped_search(
        self, request: ScopedSearchEntitySharesInput
    ) -> SearchEntitySharesPayload:
        """Search the invitations the named sides reach."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/search",
            request=request,
            response_model=SearchEntitySharesPayload,
        )
