from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession, Session
from ai.backend.test.contexts.auth import EndpointContext, KeypairContext
from ai.backend.test.contexts.client_session import ClientSessionContext, ClientSyncSessionContext
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
        keypair = KeypairContext.current()
        endpoint = EndpointContext.current()
        api_config = APIConfig(
            endpoint=endpoint.api_endpoint,
            endpoint_type="api",
            access_key=keypair.access_key,
            secret_key=keypair.secret_key,
        )

        async with AsyncSession(config=api_config) as session:
            with ClientSessionContext.with_current(session):
                yield


class KeypairAuthSyncTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "keypair_auth_sync"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        keypair = KeypairContext.current()
        endpoint = EndpointContext.current()
        api_config = APIConfig(
            endpoint=endpoint.api_endpoint,
            endpoint_type="api",
            access_key=keypair.access_key,
            secret_key=keypair.secret_key,
        )

        with Session(config=api_config) as session:
            with ClientSyncSessionContext.with_current(session):
                yield
