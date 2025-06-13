from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.config import EndpointConfigContext, KeypairConfigContext
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class KeypairAuthTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "keypair_auth"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        keypair = KeypairConfigContext.current()
        endpoint = EndpointConfigContext.current()
        api_config = APIConfig(
            endpoint=endpoint.api_endpoint,
            endpoint_type="api",
            access_key=keypair.access_key,
            secret_key=keypair.secret_key,
        )

        async with AsyncSession(config=api_config) as session:
            with ClientSessionContext.with_current(session):
                yield
