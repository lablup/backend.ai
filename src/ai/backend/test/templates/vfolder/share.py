from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.user import CreatedUserContext
from ai.backend.test.contexts.vfolder import (
    CreatedVFolderMetaContext,
    VFolderContext,
    VFolderShareContext,
)
from ai.backend.test.data.vfolder import VFolderShareMeta
from ai.backend.test.templates.template import WrapperTestTemplate
from ai.backend.test.utils.exceptions import UnexpectedFailure


class ShareVFolderTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "share_vfolder"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        vfolder_meta = CreatedVFolderMetaContext.current()
        client_session = ClientSessionContext.current()
        created_user_meta = CreatedUserContext.current()
        vfolder_dep = VFolderContext.current()
        override_permission = vfolder_dep.share_permission

        vfolder_info = await client_session.VFolder(name=vfolder_meta.name).info()
        # TODO: Move VFolderOwnershipType to common package
        if vfolder_info["type"] != "group":
            raise UnexpectedFailure("VFolder type should be 'group' for sharing.")

        try:
            await client_session.VFolder(name=vfolder_meta.name).share(
                perm=override_permission, emails=[created_user_meta.email]
            )
            with VFolderShareContext.with_current(
                VFolderShareMeta(
                    override_permission=override_permission, user_emails=[created_user_meta.email]
                )
            ):
                yield
        finally:
            await client_session.VFolder(name=vfolder_meta.name).unshare(
                emails=[created_user_meta.email]
            )
            vfolder_info = await client_session.VFolder(name=vfolder_meta.name).info()
            assert vfolder_info["permission"] == vfolder_dep.permission, (
                f"VFolder permission should be reverted to '{vfolder_dep.permission}' after unsharing."
            )
