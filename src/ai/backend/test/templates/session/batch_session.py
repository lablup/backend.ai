import asyncio
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import (
    BatchSessionContext,
    ClusterContext,
    CreatedSessionMetaContext,
    SessionContext,
)
from ai.backend.test.contexts.sse import (
    SSEContext,
)
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.data.session import CreatedSessionMeta
from ai.backend.test.templates.session.utils import verify_session_events
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class BatchSessionTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "batch_session"

    async def _verify_session_creation(
        self, client_session: AsyncSession, session_name: str
    ) -> UUID:
        image_dep = ImageContext.current()
        cluster_dep = ClusterContext.current()
        batch_dep = BatchSessionContext.current()
        sess_dep = SessionContext.current()
        timeout = SSEContext.current().timeout

        listener = asyncio.create_task(
            asyncio.wait_for(
                verify_session_events(
                    client_session,
                    session_name,
                    "session_terminated",
                    {"session_failure", "session_cancelled"},
                ),
                timeout,
            )
        )

        created = await client_session.ComputeSession.get_or_create(
            image_dep.name,
            architecture=image_dep.architecture,
            resources=sess_dep.resources,
            type_="batch",
            startup_command=batch_dep.startup_command,
            batch_timeout=batch_dep.batch_timeout,
            name=session_name,
            cluster_mode=cluster_dep.cluster_mode,
            cluster_size=cluster_dep.cluster_size,
        )

        assert created.created, "Session should be created successfully"
        assert created.name == session_name, "Session name mismatch"
        assert created.status in {"TERMINATING", "TERMINATED"}, (
            f"Unexpected final status: {created.status}"
        )
        if created.id is None:
            raise RuntimeError("Session ID is None after creation")
        await listener
        return created.id

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        client_session = ClientSessionContext.current()
        session_name = f"test_session_{str(test_id)}"

        session_id = await self._verify_session_creation(client_session, session_name)
        with CreatedSessionMetaContext.with_current(
            CreatedSessionMeta(id=session_id, name=session_name)
        ):
            yield
