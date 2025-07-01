from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
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
