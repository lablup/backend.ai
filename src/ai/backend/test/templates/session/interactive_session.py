import asyncio
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.common.json import load_json
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import AsyncSessionContext
from ai.backend.test.contexts.compute_session import (
    CreatedSessionIDContext,
    SessionCreationContextArgs,
    SessionCreationFromImageContextArgs,
)
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import (
    TestTemplate,
    WrapperTestTemplate,
)

_IMAGE_NAME = "cr.backend.ai/stable/python:3.9-ubuntu20.04"
_IMAGE_RESOURCES = {"cpu": 1, "mem": "512m"}
_TEST_TIMEOUT = 30.0  # seconds


class InteractiveSessionTemplate(WrapperTestTemplate):
    def __init__(self, template: TestTemplate) -> None:
        super().__init__(template)

    @property
    def name(self) -> str:
        return "interactive_session"

    async def _verify_session_creation(
        self,
        client_session: AsyncSession,
        creation_ctx: SessionCreationContextArgs,
        session_name: str,
    ) -> UUID:
        with AsyncSessionContext.with_current(client_session):
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

            if creation_ctx.image:
                created_session = await client_session.ComputeSession.get_or_create(
                    creation_ctx.image.canonical,
                    type_="interactive",
                    resources=creation_ctx.image.resources,
                    name=session_name,
                    cluster_mode=creation_ctx.cluster_mode,
                    cluster_size=creation_ctx.cluster_size,
                )
            else:
                assert creation_ctx.template is not None, (
                    "Session creation context must have either image or template defined"
                )

                created_session = await client_session.ComputeSession.create_from_template(
                    creation_ctx.template.template_id,
                    type_="interactive",
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
                assert created_session.status == "RUNNING", "Session should be running"

                return created_session.id
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"Timed out after {_TEST_TIMEOUT}s; events received so far: {collected_events}"
                ) from e

    async def _verify_session_destruction(
        self,
        client_session: AsyncSession,
        session_name: str,
    ) -> None:
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
                    data = load_json(event.data)
                    assert data["reason"] == "user-requested", (
                        "Session should be terminated by user request"
                    )

                    collected_events.add(event.event)
                    if collected_events == EXPECTED_EVENTS:
                        # print("All expected events received.")
                        break

        listener_task = asyncio.create_task(
            asyncio.wait_for(collect_events(), timeout=_TEST_TIMEOUT)
        )

        result = await client_session.ComputeSession(session_name).destroy()
        assert result["stats"]["status"] == "terminated", (
            f"Session should be terminated, actual reason: {result['stats']['reason']}"
        )

        try:
            await listener_task
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
            image=SessionCreationFromImageContextArgs(
                canonical=_IMAGE_NAME,
                resources=_IMAGE_RESOURCES,
            ),
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            template=None,
        )
        session_name = f"test_session_{str(test_id)}"

        async with AsyncSession() as client_session:
            try:
                session_id = await self._verify_session_creation(
                    client_session, creation_ctx, session_name
                )
                with CreatedSessionIDContext.with_current(session_id):
                    yield
            finally:
                await self._verify_session_destruction(client_session, session_name)
                pass
