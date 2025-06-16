import asyncio

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import SessionContext
from ai.backend.test.contexts.sse import (
    SSEContext,
)
from ai.backend.test.templates.template import TestCode


class BatchSessionCreationFailureWrongCommand(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        image = ImageContext.current()
        sse_config = SSEContext.current()
        session_config = SessionContext.current()

        session_name = "test-batch-session-execution-failure"

        async def collect_events():
            async with client_session.ComputeSession(session_name).listen_events() as events:
                async for event in events:
                    if event.event == "session_failure":
                        break
                    if event.event == "session_success":
                        raise RuntimeError("BatchSession should not succeed with wrong command")

        listener_task = asyncio.create_task(
            asyncio.wait_for(collect_events(), timeout=sse_config.timeout)
        )

        try:
            await client_session.ComputeSession.get_or_create(
                image.name,
                architecture=image.architecture,
                name=session_name,
                type_="batch",
                startup_command="some_wrong_command!@#123",
                resources=session_config.resources,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
            )

            await listener_task
        except BackendAPIError:
            # TODO: Should `get_or_create` raise error when the command fails?
            assert False, "Unreachable code"
