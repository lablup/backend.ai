from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionMetaContext
from ai.backend.test.templates.template import TestCode


class TestSessionRename(TestCode):
    @override
    async def test(self) -> None:
        session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()
        session_id = session_meta.id
        session_name = session_meta.name
        new_name = f"{session_name}_renamed"

        await session.ComputeSession(name=session_name).rename(new_name)
        renamed_info = await session.ComputeSession.from_session_id(session_id=session_id).detail()
        assert renamed_info["name"] == new_name

        # Clean up by renaming back to original name
        await session.ComputeSession(name=new_name).rename(session_name)
