from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override

from ai.backend.test.contexts.client_session import (
    CreatedUserClientSessionContext,
)
from ai.backend.test.contexts.user import CreatedUserContext
from ai.backend.test.contexts.vfolder import VFolderInvitationPermissionContext
from ai.backend.test.templates.template import WrapperTestTemplate


class AcceptInvitationTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "accept_invitation"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = CreatedUserClientSessionContext.current()
        created_user_meta = CreatedUserContext.current()
        mount_permission = VFolderInvitationPermissionContext.current()
        invitation_response = await client_session.VFolder.invitations()
        assert len(invitation_response["invitations"]) > 0, "No invitations found"
        invitation = invitation_response["invitations"][0]
        assert "id" in invitation, "Invitation ID not found in the response"
        assert invitation["status"] == "pending", (
            f"Invitation is not pending. Actual value: {invitation['status']}"
        )
        assert invitation["invitee_user_email"] == created_user_meta.email, (
            f"Invitation email does not match created user email. Actual value: {invitation['inviter_user_email']}"
        )
        assert invitation["mount_permission"] == mount_permission, (
            f"Invitation mount permission does not match. Actual value: {invitation['mount_permission']}"
        )

        await client_session.VFolder.accept_invitation(invitation["id"])
        yield
