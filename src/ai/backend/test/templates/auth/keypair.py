from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.auth import KeypairContext, KeypairEndpointContext
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.templates.template import WrapperTestTemplate


class KeypairTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "auth_keypair"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        keypair_ctx = KeypairContext.get_current()
        endpoint_ctx = KeypairEndpointContext.get_current()

        api_config = APIConfig(
            endpoint=endpoint_ctx.endpoint,
            endpoint_type="api",
            access_key=keypair_ctx.access_key,
            secret_key=keypair_ctx.secret_key,
        )

        async with AsyncSession(config=api_config) as session:
            with ClientSessionContext.with_current(session):
                yield
