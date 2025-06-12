import asyncio

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import AsyncSession
from ai.backend.common.types import ClusterMode
from ai.backend.test.templates.template import TestCode

# Test environment configuration
# TODO: Make these configurable loaderable by template wrapper
_IMAGE_NAME = "cr.backend.ai/stable/python:3.9-ubuntu20.04"
_TEST_TIMEOUT = 30.0  # seconds


class BatchSessionCreationFailureWrongCommand(TestCode):
    def __init__(self) -> None:
        super().__init__()

    async def test(self) -> None:
        async with AsyncSession() as client_session:
            session_name = "test-batch-session-creation-failure"

            async def collect_events():
                async with client_session.ComputeSession(session_name).listen_events() as events:
                    async for event in events:
                        if event.event == "session_failure":
                            break
                        if event.event == "session_success":
                            raise RuntimeError("BatchSession should not succeed with wrong command")

            listener_task = asyncio.create_task(
                asyncio.wait_for(collect_events(), timeout=_TEST_TIMEOUT)
            )

            try:
                await client_session.ComputeSession.get_or_create(
                    _IMAGE_NAME,
                    name=session_name,
                    type_="batch",
                    startup_command="some_wrong_command!@#123",
                    resources={"cpu": 1, "mem": "512m"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                )

                await listener_task
            except BackendAPIError:
                # TODO: Should `get_or_create` raise error when the command fails?
                assert False, "Unreachable code"
