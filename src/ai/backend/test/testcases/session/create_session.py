import asyncio
from dataclasses import dataclass

from ai.backend.client.session import AsyncSession
from ai.backend.common.types import ClusterMode
from ai.backend.test.templates.template import TestCode
from ai.backend.test.testcases.session.context import ComputeSessionContext

# Test environment configuration
# TODO: Make these configurable loaderable by template wrapper
_IMAGE_NAME = "cr.backend.ai/stable/python:3.9-ubuntu20.04"
_IMAGE_RESOURCES = {"cpu": 1, "mem": "512m"}
_TEST_TIMEOUT = 30.0  # seconds


@dataclass
class CreateSessionArgs:
    cluster_mode: ClusterMode
    cluster_size: int = 1


class CreateSession(TestCode):
    def __init__(self, args: CreateSessionArgs):
        super().__init__()
        self.args = args

    async def test(self) -> None:
        async with AsyncSession() as client_session:
            session_name = ComputeSessionContext.get_current()

            EXPECTED_EVENTS = {
                "session_enqueued",
                "session_scheduled",
                "kernel_preparing",
                "kernel_creating",
                "kernel_started",
                "session_started",
            }

            collected_events = set()

            async def collect_events():
                async with client_session.ComputeSession(session_name).listen_events() as events:
                    async for event in events:
                        collected_events.add(event.event)
                        if collected_events == EXPECTED_EVENTS:
                            # print("All expected events received.")
                            break

            listener_task = asyncio.create_task(
                asyncio.wait_for(collect_events(), timeout=_TEST_TIMEOUT)
            )

            created_session = await client_session.ComputeSession.get_or_create(
                _IMAGE_NAME,
                name=session_name,
                resources=_IMAGE_RESOURCES,
                cluster_mode=self.args.cluster_mode,
                cluster_size=self.args.cluster_size,
            )

            assert created_session.created, "Session should be created successfully"
            assert created_session.name == session_name, (
                "Session name should match the provided name"
            )

            try:
                await listener_task
                assert created_session.status == "RUNNING", "Session should be running"
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"Timed out after {_TEST_TIMEOUT}s; events received so far: {collected_events}"
                ) from e
