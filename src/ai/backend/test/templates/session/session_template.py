from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import (
    CreatedSessionTemplateIDContext,
    SessionTemplateConfigContext,
)
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class SessionTemplateTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "session_template"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        template = SessionTemplateConfigContext.current()

        try:
            result = await client_session.SessionTemplate.create(template.content)
            template_id = result.template_id

            with CreatedSessionTemplateIDContext.with_current(template_id):
                yield
        finally:
            await client_session.SessionTemplate(template_id).delete()
            pass
