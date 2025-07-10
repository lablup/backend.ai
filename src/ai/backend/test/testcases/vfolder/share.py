from ai.backend.client.session import set_api_context
from ai.backend.test.contexts.client_session import (
    ClientSessionContext,
    CreatedUserClientSessionContext,
)
from ai.backend.test.contexts.vfolder import (
    CreatedVFolderMetaContext,
    VFolderContext,
    VFolderShareContext,
)
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import UnexpectedFailure


class VFolderSharePermissionOverrideSuccess(TestCode):
    async def test(self) -> None:
        vfolder_meta = CreatedVFolderMetaContext.current()
        # The session of the user who shared the vfolder
        sharing_user_session = ClientSessionContext.current()
        # The session of the user who received the share
        shared_user_session = CreatedUserClientSessionContext.current()

        vfolder_share_dep = VFolderContext.current()
        vfolder_share_meta = VFolderShareContext.current()

        if vfolder_share_dep.permission == vfolder_share_meta.override_permission:
            raise UnexpectedFailure(
                "VFolder share permission should not match the override permission for test purposes."
            )

        # TODO: Refactor 'set_api_context' after refactoring AsyncSession(session management with contextvars)
        async with set_api_context(sharing_user_session):
            sharing_user_vfolder_info = await sharing_user_session.VFolder(
                name=vfolder_meta.name
            ).info()
            assert sharing_user_vfolder_info["permission"] == vfolder_share_dep.permission

        async with set_api_context(shared_user_session):
            shared_user_vfolder_info = await shared_user_session.VFolder(
                name=vfolder_meta.name
            ).info()
            assert shared_user_vfolder_info["permission"] == vfolder_share_meta.override_permission
