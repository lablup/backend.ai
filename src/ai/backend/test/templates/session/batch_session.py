import asyncio
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.session import AsyncSession
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import AsyncSessionContext
from ai.backend.test.contexts.compute_session import (
    SessionCreationContextArgs,
)
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import (
    TestTemplate,
    WrapperTestTemplate,
)

_IMAGE_NAME = "cr.backend.ai/stable/python:3.9-ubuntu20.04"
_IMAGE_RESOURCES = {"cpu": 1, "mem": "512m"}
_TEST_TIMEOUT = 30.0  # seconds


class BatchSessionTemplate(WrapperTestTemplate):
    def __init__(self, template: TestTemplate) -> None:
        super().__init__(template)

    @property
    def name(self) -> str:
        return "create_session"

    async def _verify_session_creation(
        self,
        client_session: AsyncSession,
        creation_ctx: SessionCreationContextArgs,
        session_name: str,
    ) -> None:
        with AsyncSessionContext.with_current(client_session):
            EXPECTED_EVENTS = {
                "session_enqueued",
                "session_scheduled",
                "kernel_preparing",
                "kernel_creating",
                "kernel_started",
                "session_started",
                "session_terminating",
                "session_terminated",
                "kernel_terminating",
                "kernel_terminated",
                "session_success",
            }

            collected_events = set()

            async def collect_events():
                async with client_session.ComputeSession(session_name).listen_events() as events:
                    async for event in events:
                        collected_events.add(event.event)
                        if event.event == "session_failure":
                            raise RuntimeError(f"BatchSession failed with event: {event.event}")

                        if collected_events == EXPECTED_EVENTS:
                            # print("All expected events received.")
                            break

            listener_task = asyncio.create_task(
                asyncio.wait_for(collect_events(), timeout=_TEST_TIMEOUT)
            )

            created_session = await client_session.ComputeSession.get_or_create(
                creation_ctx.image_canonical,
                type_="batch",
                startup_command="ls -la",
                resources=creation_ctx.image_resources,
                name=session_name,
                cluster_mode=creation_ctx.cluster_mode,
                cluster_size=creation_ctx.cluster_size,
            )

            assert created_session.created, "Session should be created successfully"
            assert created_session.name == session_name, (
                "Session name should match the provided name"
            )

            try:
                await listener_task
                assert created_session.status in ["TERMINATING", "TERMINATED"], (
                    f"Session should be terminiated or terminiating, actual status: {created_session.status}"
                )
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"Timed out after {_TEST_TIMEOUT}s; events received so far: {collected_events}"
                ) from e

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        test_id = TestIDContext.get_current()
        # TODO: After the refactoring, we can use the creation context instead of hardcoding
        # creation_ctx = SessionCreationContext.get_current()
        creation_ctx = SessionCreationContextArgs(
            image_canonical=_IMAGE_NAME,
            image_resources=_IMAGE_RESOURCES,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
        )
        session_name = f"test_session_{str(test_id)}"

        async with AsyncSession() as client_session:
            await self._verify_session_creation(client_session, creation_ctx, session_name)
            yield
