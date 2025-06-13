import asyncio

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.compute_session import SessionCreationContext
from ai.backend.test.templates.template import TestCode


class BatchSessionCreationFailureWrongCommand(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        creation_args = SessionCreationContext.current()

        session_name = "test-batch-session-execution-failure"

        async def collect_events():
            async with client_session.ComputeSession(session_name).listen_events() as events:
                async for event in events:
                    if event.event == "session_failure":
                        break
                    if event.event == "session_success":
                        raise RuntimeError("BatchSession should not succeed with wrong command")

        listener_task = asyncio.create_task(
            asyncio.wait_for(collect_events(), timeout=creation_args.timeout)
        )

        try:
            await client_session.ComputeSession.get_or_create(
                creation_args.image,
                name=session_name,
                type_="batch",
                startup_command="some_wrong_command!@#123",
                resources=creation_args.resources,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
            )

            await listener_task
        except BackendAPIError:
            # TODO: Should `get_or_create` raise error when the command fails?
            assert False, "Unreachable code"
