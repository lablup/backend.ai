"""V2 SDK client for role invitations."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CreateRoleInvitationInput,
    SearchRoleInvitationsInput,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    CreateRoleInvitationPayload,
    RoleInvitationNode,
    SearchRoleInvitationsPayload,
)

_PATH = "/v2/role-invitations"


class V2RoleInvitationClient(BaseDomainClient):
    """SDK client for ``/v2/role-invitations`` endpoints."""

    async def create(
        self,
        request: CreateRoleInvitationInput,
    ) -> CreateRoleInvitationPayload:
        """Create role invitations by email."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateRoleInvitationPayload,
        )

    async def accept(self, invitation_id: UUID) -> RoleInvitationNode:
        """Accept a pending invitation."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{invitation_id}/accept",
            response_model=RoleInvitationNode,
        )

    async def reject(self, invitation_id: UUID) -> RoleInvitationNode:
        """Reject a pending invitation."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{invitation_id}/reject",
            response_model=RoleInvitationNode,
        )

    async def cancel(self, invitation_id: UUID) -> RoleInvitationNode:
        """Cancel a pending invitation."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{invitation_id}",
            response_model=RoleInvitationNode,
        )

    async def my_search(
        self,
        request: SearchRoleInvitationsInput,
    ) -> SearchRoleInvitationsPayload:
        """Search invitations addressed to the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=SearchRoleInvitationsPayload,
        )

    async def role_search(
        self,
        role_id: UUID,
        request: SearchRoleInvitationsInput,
    ) -> SearchRoleInvitationsPayload:
        """Search invitations for a specific role."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/roles/{role_id}/search",
            request=request,
            response_model=SearchRoleInvitationsPayload,
        )
