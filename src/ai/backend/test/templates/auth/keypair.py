from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.auth import EndpointContext, KeypairContext
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.templates.template import (
    TestTemplate,
    WrapperTestTemplate,
    WrapperTestTemplateProtocol,
)


class KeypairAuthTemplate(WrapperTestTemplate):
    # TODO: How to Remove this?
    def __init__(
        self, template: TestTemplate, wrapper_templates: list["WrapperTestTemplateProtocol"] = []
    ) -> None:
        super().__init__(template, wrapper_templates)

    @property
    def name(self) -> str:
        return "keypair_auth"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        keypair_ctx = KeypairContext.get_current()
        endpoint_ctx = EndpointContext.get_current()
        api_config = APIConfig(
            endpoint=endpoint_ctx.api_endpoint,
            endpoint_type="api",
            access_key=keypair_ctx.access_key,
            secret_key=keypair_ctx.secret_key,
        )

        async with AsyncSession(config=api_config) as session:
            with ClientSessionContext.with_current(session):
                yield
