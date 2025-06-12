from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.session import AsyncSession
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.compute_session import (
    SessionCreationContext,
    SessionCreationContextArgs,
    SessionCreationFromTemplateContextArgs,
)
from ai.backend.test.templates.template import (
    TestTemplate,
    WrapperTestTemplate,
)


class SessionTemplateTemplate(WrapperTestTemplate):
    def __init__(self, template: TestTemplate) -> None:
        super().__init__(template)

    @property
    def name(self) -> str:
        return "session_template"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        # TODO: After the refactoring, we can use the creation context instead of hardcoding
        # template_ctx = SessionCreationContext.get_current()

        template_obj = [
            {
                "id": "c1b8441a-ba46-4a83-8727-de6645f521b4",
                "is_active": True,
                "domain_name": "default",
                "group_id": "2de2b969-1d04-48a6-af16-0bc8adb3c831",
                "user_uuid": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
                "type": "TASK",
                "name": "python_x86",
                "template": {
                    "api_version": "6",
                    "kind": "task_template",
                    "metadata": {
                        "name": "cr.backend.ai/multiarch/python",
                        "tag": "3.10-ubuntu20.04",
                    },
                    "spec": {
                        "session_type": "interactive",
                        "kernel": {
                            "image": "cr.backend.ai/multiarch/python:3.10-ubuntu20.04",
                            "environ": {},
                            "architecture": "x86_64",
                            "run": None,
                            "git": None,
                        },
                        "scaling_group": "default",
                        "mounts": {},
                        "resources": {"cpu": "2", "mem": "4g"},
                    },
                },
            }
        ]

        template = dump_json_str(template_obj)

        async with AsyncSession() as client_session:
            try:
                result = await client_session.SessionTemplate.create(template)
                template_id = result.template_id

                session_creation_ctx = SessionCreationContextArgs(
                    image=None,
                    template=SessionCreationFromTemplateContextArgs(
                        content=template,
                        template_id=template_id,
                    ),
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                )

                with SessionCreationContext.with_current(session_creation_ctx):
                    yield
            finally:
                await client_session.SessionTemplate(template_id).delete()
                pass
