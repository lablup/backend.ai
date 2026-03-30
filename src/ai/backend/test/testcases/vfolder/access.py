from ai.backend.client.exceptions import BackendAPIError
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import (
    CreatedVFolderMetaContext,
    VFolderInvitationPermissionContext,
)
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import UnexpectedSuccess


class VFolderAccessSuccess(TestCode):
    """
    Test whether logged-in user can access the vfolder properly.
    """

    async def test(self) -> None:
        vfolder_meta = CreatedVFolderMetaContext.current()
        client_session = ClientSessionContext.current()
        permission = VFolderInvitationPermissionContext.current()

        vfolder_info = await client_session.VFolder(vfolder_meta.name).info()

        assert vfolder_info["id"] == vfolder_meta.id, (
            f"VFolder ID does not match expected value: "
            f"expected {vfolder_meta.id}, actual {vfolder_info['id']}"
        )
        assert vfolder_info["name"] == vfolder_meta.name, (
            f"VFolder name does not match expected value: "
            f"expected {vfolder_meta.name}, actual {vfolder_info['name']}"
        )
        assert vfolder_info["permission"] == permission, (
            f"VFolder permission does not match expected value: "
            f"expected {permission}, actual {vfolder_info['permission']}"
        )


class VFolderAccessFailure(TestCode):
    async def test(self) -> None:
        vfolder_meta = CreatedVFolderMetaContext.current()
        client_session = ClientSessionContext.current()

        try:
            await client_session.VFolder(vfolder_meta.name).info()
            raise UnexpectedSuccess("VFolder access should have failed, but it succeeded.")
        except BackendAPIError as e:
            assert e.status == 404, f"Expected 404 error, but got {e.status}: Exception: {e}"
