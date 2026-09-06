"""V2 SDK client for the entity invitation domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    CreateEntityInvitationInput,
    ScopedSearchEntityInvitationsInput,
)
from ai.backend.common.dto.manager.v2.entity_invitation.response import (
    EntityInvitationPayload,
    SearchEntityInvitationsPayload,
)

_PATH = "/v2/entity-invitations"


class V2EntityInvitationClient(BaseDomainClient):
    """SDK client for entity invitation operations."""

    async def create(self, request: CreateEntityInvitationInput) -> EntityInvitationPayload:
        """Offer one entity to one address."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=EntityInvitationPayload,
        )

    async def get(self, invitation_id: UUID) -> EntityInvitationPayload:
        """Read one invitation from the side that offered it."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{invitation_id}",
            response_model=EntityInvitationPayload,
        )

    async def accept(self, invitation_id: UUID) -> EntityInvitationPayload:
        """Take what was offered."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{invitation_id}/accept",
            response_model=EntityInvitationPayload,
        )

    async def reject(self, invitation_id: UUID) -> EntityInvitationPayload:
        """Turn down what was offered."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{invitation_id}/reject",
            response_model=EntityInvitationPayload,
        )

    async def cancel(self, invitation_id: UUID) -> EntityInvitationPayload:
        """Withdraw the offer before it was answered."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{invitation_id}",
            response_model=EntityInvitationPayload,
        )

    async def scoped_search(
        self, request: ScopedSearchEntityInvitationsInput
    ) -> SearchEntityInvitationsPayload:
        """Search the invitations the named sides reach."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/scoped/search",
            request=request,
            response_model=SearchEntityInvitationsPayload,
        )
