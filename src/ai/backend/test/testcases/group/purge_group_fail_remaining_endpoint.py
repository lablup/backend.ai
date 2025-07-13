from typing import override

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.group import CreatedGroupContext
from ai.backend.test.templates.template import TestCode


class PurgeGroupFailRemainingActiveEndpointExist(TestCode):
    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        created_group_meta = CreatedGroupContext.current()

        try:
            await client_session.Group.purge(str(created_group_meta.group_id))
        except BackendAPIError as e:
            assert e.status == 400, (
                "Expected a 400 Bad Request error when purging a group with active endpoints."
            )


class PurgeGroupFailRemainingActiveSessionExist(TestCode):
    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        created_group_meta = CreatedGroupContext.current()

        try:
            await client_session.Group.purge(str(created_group_meta.group_id))
        except BackendAPIError as e:
            assert e.status == 400, (
                "Expected a 400 Bad Request error when purging a group with active sessions."
            )
