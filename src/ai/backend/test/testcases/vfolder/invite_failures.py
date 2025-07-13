from ai.backend.client.exceptions import BackendAPIError
from ai.backend.test.contexts.client_session import (
    ClientSessionContext,
    CreatedUserClientSessionContext,
)
from ai.backend.test.contexts.user import CreatedUserContext
from ai.backend.test.contexts.vfolder import (
    CreatedVFolderMetaContext,
    VFolderInvitationPermissionContext,
)
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import UnexpectedSuccess


class VFolderInviteFailure(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        test_user = CreatedUserContext.current()
        perm = VFolderInvitationPermissionContext.current()

        try:
            await client_session.VFolder(vfolder_meta.name).invite(
                perm=perm, emails=[test_user.email]
            )
        except BackendAPIError as e:
            assert e.status == 404, f"Expected 404 error, but got {e.status}: Exception: {e}"


class VFolderAcceptDuplicatedInvitation(TestCode):
    async def test(self) -> None:
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

        try:
            await client_session.VFolder.accept_invitation(invitation["id"])
            raise UnexpectedSuccess("Invitation was accepted again, but it should have failed.")
        except BackendAPIError as e:
            assert e.status == 404, f"Expected 404 error, but got {e.status}: Exception: {e}"
