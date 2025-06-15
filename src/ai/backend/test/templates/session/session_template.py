import textwrap
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageConfigContext
from ai.backend.test.contexts.session import (
    CreatedSessionTemplateIDContext,
    SessionConfigContext,
)
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class SessionTemplateTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "session_template"

    def build_json_template(self, session_type: str) -> str:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        image = ImageConfigContext.current()

        if image.name is None:
            raise ValueError("Image name is not set in ImageConfigContext.")
        image_name = image.name.split(":")[0]
        image_tag = image.name.split(":")[1]
        session_config = SessionConfigContext.current()

        if session_config.resources is None:
            raise ValueError("SessionConfigContext resources are not set.")

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
                                "image": "{image.name}",
                                "environ": {{}},
                                "architecture": "{image.architecture}"
                            }},
                            "scaling_group": "default",
                            "mounts": {{}},
                            "resources": {{
                                "cpu": "{session_config.resources["cpu"]}",
                                "mem": "{session_config.resources["mem"]}"
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
        template = self.build_json_template(session_type="interactive")

        try:
            result = await client_session.SessionTemplate.create(template)
            template_id = result.template_id

            with CreatedSessionTemplateIDContext.with_current(template_id):
                yield
        finally:
            await client_session.SessionTemplate(template_id).delete()
            pass
