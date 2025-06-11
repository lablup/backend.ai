import asyncio
import json

from ai.backend.client.session import AsyncSession
from ai.backend.test.templates.template import TestCode
from ai.backend.test.testcases.session.context import ComputeSessionContext

# Test environment configuration
# TODO: Make these configurable loaderable by template wrapper
_TEST_TIMEOUT = 30.0  # seconds


class DestroySession(TestCode):
    async def test(self) -> None:
        async with AsyncSession() as client_session:
            session_name = ComputeSessionContext.get_current()

            EXPECTED_EVENTS = {
                "session_terminating",
                "session_terminated",
                "kernel_terminating",
                "kernel_terminated",
            }

            collected_events = set()

            async def collect_events():
                async with client_session.ComputeSession(session_name).listen_events() as events:
                    async for event in events:
                        data = json.loads(event.data)
                        assert data["reason"] == "user-requested", (
                            "Session should be terminated by user request"
                        )

                        collected_events.add(event.event)
                        if collected_events == EXPECTED_EVENTS:
                            print("All expected events received.")
                            break

            listener_task = asyncio.create_task(
                asyncio.wait_for(collect_events(), timeout=_TEST_TIMEOUT)
            )

            result = await client_session.ComputeSession(session_name).destroy()
            assert result["stats"]["status"] == "terminated", "Session should be terminated"

            try:
                await listener_task
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"Timed out after {_TEST_TIMEOUT}s; events received so far: {collected_events}"
                ) from e
