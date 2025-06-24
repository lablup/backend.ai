import asyncio
import textwrap
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
    CreatedSessionTemplateIDContext,
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
from ai.backend.test.utils.exceptions import DependencyNotSet


class SessionTemplateTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "session_template"

    def _build_json_template(self, session_type: str) -> str:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        image_dep = ImageContext.current()
        image_name = image_dep.name.split(":")[0]
        image_tag = image_dep.name.split(":")[1]
        session_dep = SessionContext.current()

        if session_dep.resources is None:
            raise DependencyNotSet("SessionConfigContext resources are not set.")

        return textwrap.dedent(f"""
            [
                {{
                    "is_active": true,
                    "type": "TASK",
                    "name": "test_session_template_{test_id}",
                    "template": {{
                        "api_version": "6",
                        "kind": "task_template",
                        "metadata": {{
                            "name": "{image_name}",
                            "tag": "{image_tag}"
                        }},
                        "spec": {{
                            "session_type": "{session_type}",
                            "kernel": {{
                                "image": "{image_dep.name}",
                                "environ": {{}},
                                "architecture": "{image_dep.architecture}"
                            }},
                            "scaling_group": "default",
                            "mounts": {{}},
                            "resources": {{
                                "cpu": "{session_dep.resources["cpu"]}",
                                "mem": "{session_dep.resources["mem"]}"
                            }}
                        }}
                    }}
                }}
            ]
        """)

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        # TODO: Inject session type from contextvar
        template = self._build_json_template(session_type="interactive")

        template_id = None
        try:
            result = await client_session.SessionTemplate.create(template)
            template_id = result.template_id

            with CreatedSessionTemplateIDContext.with_current(template_id):
                yield
        finally:
            if template_id:
                await client_session.SessionTemplate(template_id).delete()
            pass


class BatchSessionFromTemplateTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "batch_session_from_template"

    async def _verify_session_creation(
        self, client_session: AsyncSession, session_name: str
    ) -> UUID:
        cluster_cfg = ClusterContext.current()
        batch_cfg = BatchSessionContext.current()
        template_id = CreatedSessionTemplateIDContext.current()
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

        created = await client_session.ComputeSession.create_from_template(
            template_id,
            type_="batch",
            startup_command=batch_cfg.startup_command,
            name=session_name,
            cluster_mode=cluster_cfg.cluster_mode,
            cluster_size=cluster_cfg.cluster_size,
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


class InteractiveSessionFromTemplateTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "interactive_session_from_template"

    async def _verify_session_creation(
        self, client_session: AsyncSession, session_name: str
    ) -> UUID:
        cluster_cfg = ClusterContext.current()
        timeout = SSEContext.current().timeout
        template_id = CreatedSessionTemplateIDContext.current()

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

        created = await client_session.ComputeSession.create_from_template(
            template_id,
            type_="interactive",
            name=session_name,
            cluster_mode=cluster_cfg.cluster_mode,
            cluster_size=cluster_cfg.cluster_size,
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
        try:
            session_id = await self._verify_session_creation(client_session, session_name)
            with CreatedSessionMetaContext.with_current(
                CreatedSessionMeta(id=session_id, name=session_name)
            ):
                yield
        finally:
            if session_id:
                await self._verify_session_destruction(client_session, session_name)
