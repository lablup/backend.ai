import asyncio
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import (
    ClusterContext,
    CreatedSessionMetaContext,
    SessionContext,
    SessionDependencyContext,
)
from ai.backend.test.contexts.sse import SSEContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.data.session import CreatedSessionMeta, SessionDependency
from ai.backend.test.templates.session.utils import verify_session_events
from ai.backend.test.templates.template import WrapperTestTemplate


class DependentSessionTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "dependent_session"

    async def _verify_session_creation(
        self, client_session: AsyncSession, session_name: str, dependencies: list[str]
    ) -> UUID:
        image_dep = ImageContext.current()
        cluster_dep = ClusterContext.current()
        session_dep = SessionContext.current()
        timeout = SSEContext.current().timeout

        listener = asyncio.create_task(
            asyncio.wait_for(
                verify_session_events(
                    client_session,
                    session_name,
                    "session_started",
                    {"session_failure", "session_cancelled"},
                ),
                timeout,
            )
        )

        created = await client_session.ComputeSession.get_or_create(
            image_dep.name,
            resources=session_dep.resources,
            type_="interactive",
            name=session_name,
            cluster_mode=cluster_dep.cluster_mode,
            cluster_size=cluster_dep.cluster_size,
            dependencies=dependencies,
        )

        assert created.created, "Session creation failed"
        assert created.name == session_name

        assert created.status == "RUNNING", f"Expected RUNNING, got {created.status}"
        if created.id is None:
            raise RuntimeError("Session ID is None after creation")
        await listener
        return created.id

    async def _verify_session_destruction(
        self, client_session: AsyncSession, session_name: str
    ) -> None:
        timeout = SSEContext.current().timeout

        listener = asyncio.create_task(
            asyncio.wait_for(
                verify_session_events(
                    client_session,
                    session_name,
                    "session_terminated",
                    {"session_failure", "session_cancelled"},
                    expected_termination_reason="user-requested",
                ),
                timeout,
            )
        )

        result = await client_session.ComputeSession(session_name).destroy()
        assert result["stats"]["status"] == "terminated", (
            f"Expected terminated, got {result['stats']}"
        )
        await listener

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        client_session = ClientSessionContext.current()
        session_name = f"test_session_{str(test_id)}"
        session_id = None
        batch_session_meta = CreatedSessionMetaContext.current()
        try:
            session_id = await self._verify_session_creation(
                client_session=client_session,
                session_name=session_name,
                dependencies=[batch_session_meta.name],
            )
            session_meta = CreatedSessionMeta(name=session_name, id=session_id)
            with SessionDependencyContext.with_current(
                SessionDependency(dependencies={session_meta: [batch_session_meta]})
            ):
                yield
        finally:
            if session_id:
                await self._verify_session_destruction(client_session, session_name)
