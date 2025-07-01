from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override

from ai.backend.test.contexts.client_session import (
    CreatedUserClientSessionContext,
)
from ai.backend.test.templates.template import WrapperTestTemplate


class AcceptInvitationTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "accept_invitation"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = CreatedUserClientSessionContext.current()
        invitation_response = await client_session.VFolder.invitations()
        assert len(invitation_response["invitations"]) > 0, "No invitations found"
        invitation = invitation_response["invitations"][0]
        assert "id" in invitation, "Invitation ID not found in the response"

        await client_session.VFolder.accept_invitation(invitation["id"])
        yield
