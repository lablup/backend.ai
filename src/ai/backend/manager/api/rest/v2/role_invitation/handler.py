"""REST v2 handler for role invitations."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CreateRoleInvitationInput,
    SearchRoleInvitationsInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import InvitationIdPathParam, RoleIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2RoleInvitationHandler:
    """REST v2 handler for role invitation operations."""

    def __init__(self, *, adapter: RBACAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateRoleInvitationInput],
    ) -> APIResponse:
        """Create role invitations by email."""
        result = await self._adapter.create_role_invitation(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def accept(
        self,
        path: PathParam[InvitationIdPathParam],
    ) -> APIResponse:
        """Invitee accepts a pending invitation."""
        result = await self._adapter.accept_role_invitation(path.parsed.invitation_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def reject(
        self,
        path: PathParam[InvitationIdPathParam],
    ) -> APIResponse:
        """Invitee rejects a pending invitation."""
        result = await self._adapter.reject_role_invitation(path.parsed.invitation_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def cancel(
        self,
        path: PathParam[InvitationIdPathParam],
    ) -> APIResponse:
        """Admin cancels a pending invitation."""
        result = await self._adapter.cancel_role_invitation(path.parsed.invitation_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self,
        body: BodyParam[SearchRoleInvitationsInput],
    ) -> APIResponse:
        """Search invitations addressed to the current user."""
        result = await self._adapter.my_search_role_invitations(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_sent_search(
        self,
        body: BodyParam[SearchRoleInvitationsInput],
    ) -> APIResponse:
        """Search invitations sent by the current user."""
        result = await self._adapter.my_sent_search_role_invitations(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def role_search(
        self,
        path: PathParam[RoleIdPathParam],
        body: BodyParam[SearchRoleInvitationsInput],
    ) -> APIResponse:
        """Search invitations for a specific role (admin view)."""
        result = await self._adapter.role_search_invitations(path.parsed.role_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchRoleInvitationsInput],
    ) -> APIResponse:
        """Search all invitations across the system (superadmin only)."""
        result = await self._adapter.admin_search_role_invitations(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
