from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.auth import EndpointContext, KeypairContext
from ai.backend.test.contexts.client_session import (
    ClientSessionContext,
    CreatedUserClientSessionContext,
)
from ai.backend.test.contexts.user import CreatedUserContext
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


class KeypairAuthAsCreatedUserTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "keypair_auth_as_created_user"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        credential_dep = CreatedUserContext.current()
        endpoint_dep = EndpointContext.current()

        api_config = APIConfig(
            endpoint=endpoint_dep.api_endpoint,
            endpoint_type="api",
            access_key=credential_dep.access_key,
            secret_key=credential_dep.secret_key,
        )

        async with AsyncSession(config=api_config) as session:
            with CreatedUserClientSessionContext.with_current(session):
                yield
