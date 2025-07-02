from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override

from ai.backend.test.contexts.client_session import (
    ClientSessionContext,
    CreatedUserClientSessionContext,
)
from ai.backend.test.contexts.user import CreatedUserContext
from ai.backend.test.contexts.vfolder import (
    CreatedVFolderMetaContext,
    VFolderInvitationContext,
    VFolderInvitationPermissionContext,
)
from ai.backend.test.data.vfolder import VFolderInvitationMeta
from ai.backend.test.templates.template import WrapperTestTemplate


class VFolderInviteTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "vfolder_invite"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        test_user = CreatedUserContext.current()
        perm = VFolderInvitationPermissionContext.current()

        response = await client_session.VFolder(vfolder_meta.name).invite(
            perm=perm, emails=[test_user.email]
        )
        assert "invited_ids" in response, (
            f"Response does not contain 'invited_ids', Actual value: {response}"
        )
        invited_ids = response["invited_ids"]

        invitation_meta = VFolderInvitationMeta(
            invited_user_emails=invited_ids,
        )

        with VFolderInvitationContext.with_current(invitation_meta):
            yield


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


class RejectInvitationTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "reject_invitation"

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

        await client_session.VFolder.delete_invitation(invitation["id"])
        yield
