import asyncio
from abc import abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.group import CreatedGroupContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import (
    BootstrapScriptContext,
    ClusterContext,
    CreatedSessionMetaContext,
    SessionContext,
)
from ai.backend.test.contexts.sse import (
    SSEContext,
)
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.data.session import CreatedSessionMeta
from ai.backend.test.templates.session.utils import (
    verify_session_events,
)
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class _BaseInteractiveSessionTemplate(WrapperTestTemplate):
    def _build_session_params(
        self,
        session_name: str,
    ) -> dict[str, Any]:
        image_dep = ImageContext.current()
        cluster_dep = ClusterContext.current()
        session_dep = SessionContext.current()

        params: dict[str, Any] = {
            "image": image_dep.name,
            "resources": session_dep.resources,
            "type_": "interactive",
            "name": session_name,
            "cluster_mode": cluster_dep.cluster_mode,
            "cluster_size": cluster_dep.cluster_size,
        }
        params.update(self._extra_session_params())
        return params

    @abstractmethod
    def _extra_session_params(self) -> dict[str, Any]:
        raise NotImplementedError("Subclasses must implement the _extra_session_params method.")

    async def _verify_session_creation(
        self, client_session: AsyncSession, session_name: str
    ) -> UUID:
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
            **self._build_session_params(session_name),
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
        session_name = f"test_session_{spec_meta.test_id}"
        client_session = ClientSessionContext.current()
        session_id: Optional[UUID] = None

        try:
            session_id = await self._verify_session_creation(client_session, session_name)
            with CreatedSessionMetaContext.with_current(
                CreatedSessionMeta(id=session_id, name=session_name)
            ):
                yield
        finally:
            if session_id:
                await self._verify_session_destruction(client_session, session_name)


class InteractiveSessionTemplate(_BaseInteractiveSessionTemplate):
    @property
    def name(self) -> str:
        return "interactive_session"

    @override
    def _extra_session_params(self) -> dict[str, Any]:
        return {}


class InteractiveSessionWithBootstrapScriptTemplate(_BaseInteractiveSessionTemplate):
    @property
    def name(self) -> str:
        return "interactive_session_with_bootstrap_script"

    @override
    def _extra_session_params(self) -> dict[str, Any]:
        script_ctx = BootstrapScriptContext.current()
        return {"bootstrap_script": script_ctx.bootstrap_script}


class InteractiveSessionWithCustomGroupTemplate(_BaseInteractiveSessionTemplate):
    @property
    def name(self) -> str:
        return "interactive_session_with_custom_group"

    @override
    def _extra_session_params(self) -> dict[str, Any]:
        created_group_meta = CreatedGroupContext.current()
        print(f"Creating endpoint for group: {created_group_meta.group_name}")
        return {"group_name": created_group_meta.group_name}
