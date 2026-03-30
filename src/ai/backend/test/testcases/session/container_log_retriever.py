from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionMetaContext
from ai.backend.test.templates.template import TestCode


class TestContainerLogRetriever(TestCode):
    @override
    async def test(self) -> None:
        session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()
        session_id = session_meta.id
        session_name = session_meta.name

        session_info = await session.ComputeSession.from_session_id(session_id=session_id).detail()
        kernels_info = session_info["kernels"]
        for kernel in kernels_info:
            result = await session.ComputeSession(name=session_name).get_logs(
                kernel_id=kernel["row_id"]
            )
            assert result["result"]["logs"] is not None
            assert result["result"]["logs"] != ""
