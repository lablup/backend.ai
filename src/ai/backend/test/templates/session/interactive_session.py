import asyncio
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.common.json import load_json
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.config import (
    ClusterConfigContext,
    CreatedSessionIDContext,
    CreatedSessionTemplateIDContext,
    ImageConfigContext,
    SessionConfigContext,
    SSEConfigContext,
)
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class InteractiveSessionTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "interactive_session"

    async def _verify_session_creation(
        self,
        client_session: AsyncSession,
        session_name: str,
    ) -> UUID:
        image_config = ImageConfigContext.current()
        cluster_configs = ClusterConfigContext.current()
        sse_config = SSEConfigContext.current()
        session_config = SessionConfigContext.current()

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
            asyncio.wait_for(collect_events(), timeout=sse_config.timeout)
        )

        if template := CreatedSessionTemplateIDContext.current_or_none():
            created_session = await client_session.ComputeSession.create_from_template(
                template,
                type_="interactive",
                name=session_name,
                cluster_mode=cluster_configs.cluster_mode,
                cluster_size=cluster_configs.cluster_size,
            )
        else:
            created_session = await client_session.ComputeSession.get_or_create(
                image_config.name,
                resources=session_config.resources,
                type_="interactive",
                name=session_name,
                cluster_mode=cluster_configs.cluster_mode,
                cluster_size=cluster_configs.cluster_size,
            )

        assert created_session.created, "Session should be created successfully"
        assert created_session.name == session_name, "Session name should match the provided name"

        try:
            await listener_task
            assert created_session.status == "RUNNING", "Session should be running"

            return created_session.id
        except asyncio.TimeoutError as e:
            raise asyncio.TimeoutError(
                f"Timed out after {sse_config.timeout}s; events received so far: {collected_events}"
            ) from e

    async def _verify_session_destruction(
        self,
        client_session: AsyncSession,
        session_name: str,
    ) -> None:
        sse_config = SSEConfigContext.current()
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
                        f"Session should be terminated by user request, Actual reason: {data['reason']}"
                    )

                    collected_events.add(event.event)
                    if collected_events == EXPECTED_EVENTS:
                        # print("All expected events received.")
                        break

        listener_task = asyncio.create_task(
            asyncio.wait_for(collect_events(), timeout=sse_config.timeout)
        )

        result = await client_session.ComputeSession(session_name).destroy()
        assert result["stats"]["status"] == "terminated", (
            f"Session should be terminated, actual reason: {result['stats']['reason']}"
        )

        try:
            await listener_task
        except asyncio.TimeoutError as e:
            raise asyncio.TimeoutError(
                f"Timed out after {sse_config.timeout}s; events received so far: {collected_events}"
            ) from e

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        test_id = TestIDContext.current()
        client_session = ClientSessionContext.current()
        session_name = f"test_session_{str(test_id)}"
        try:
            session_id = await self._verify_session_creation(client_session, session_name)
            with CreatedSessionIDContext.with_current(session_id):
                yield
        finally:
            await self._verify_session_destruction(client_session, session_name)
            pass
