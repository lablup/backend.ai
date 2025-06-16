from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import (
    ClusterContext,
    CreatedSessionIDContext,
    SessionContext,
)
from ai.backend.test.contexts.sse import (
    SSEContext,
)
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.templates.session.utils import (
    verify_interactive_session_creation,
    verify_interactive_session_destruction,
)
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class InteractiveSessionTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "interactive_session"

    async def _verify_session_creation(
        self, client_session: AsyncSession, session_name: str
    ) -> UUID:
        image_cfg = ImageContext.current()
        cluster_cfg = ClusterContext.current()
        session_cfg = SessionContext.current()
        timeout = SSEContext.current().timeout

        async def create_session():
            return await client_session.ComputeSession.get_or_create(
                image_cfg.name,
                resources=session_cfg.resources,
                type_="interactive",
                name=session_name,
                cluster_mode=cluster_cfg.cluster_mode,
                cluster_size=cluster_cfg.cluster_size,
            )

        return await verify_interactive_session_creation(
            client_session, session_name, timeout, create_session
        )

    async def _verify_session_destruction(
        self, client_session: AsyncSession, session_name: str
    ) -> None:
        timeout = SSEContext.current().timeout
        await verify_interactive_session_destruction(client_session, session_name, timeout)

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        client_session = ClientSessionContext.current()
        session_name = f"test_session_{str(test_id)}"
        session_id = None
        try:
            session_id = await self._verify_session_creation(client_session, session_name)
            with CreatedSessionIDContext.with_current(session_id):
                yield
        finally:
            if session_id:
                await self._verify_session_destruction(client_session, session_name)
            pass
