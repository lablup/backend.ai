"""V2 SDK client for the entity share domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.entity_share.request import (
    CreateEntityShareInput,
    MySearchEntitySharesInput,
    ScopedSearchEntitySharesInput,
)
from ai.backend.common.dto.manager.v2.entity_share.response import (
    EntitySharePayload,
    SearchEntitySharesPayload,
)

_PATH = "/v2/entity-shares"


class V2EntityShareClient(BaseDomainClient):
    """SDK client for entity share operations."""

    async def create(self, request: CreateEntityShareInput) -> EntitySharePayload:
        """Offer one entity to one address."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=EntitySharePayload,
        )

    async def get(self, share_id: UUID) -> EntitySharePayload:
        """Read one share from the side that offered it."""
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

    async def revoke(self, share_id: UUID) -> EntitySharePayload:
        """Take back what was lent."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{share_id}/revoke",
            response_model=EntitySharePayload,
        )

    async def leave(self, share_id: UUID) -> EntitySharePayload:
        """Give back what was taken."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{share_id}/leave",
            response_model=EntitySharePayload,
        )

    async def cancel(self, share_id: UUID) -> EntitySharePayload:
        """Withdraw the offer before it was answered."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{share_id}",
            response_model=EntitySharePayload,
        )

    async def my_search(self, request: MySearchEntitySharesInput) -> SearchEntitySharesPayload:
        """The shares the caller stands on a side of."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=SearchEntitySharesPayload,
        )

    async def scoped_search(
        self, request: ScopedSearchEntitySharesInput
    ) -> SearchEntitySharesPayload:
        """Search the shares the named scopes reach."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/search",
            request=request,
            response_model=SearchEntitySharesPayload,
        )
