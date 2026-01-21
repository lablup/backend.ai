from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    CreatedModelServiceEndpointMetaContext,
    CreatedModelServiceTokenContext,
)
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)

_TOKEN_DURATION = "3600"  # 1 hour


class ModelServiceTokenTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "generate_model_service_token"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        service_meta = CreatedModelServiceEndpointMetaContext.current()

        result = await client_session.Service(service_meta.service_id).generate_api_token(
            duration=_TOKEN_DURATION
        )
        assert "token" in result, (
            f"Token generation failed, 'token' not in result, Actual result: {result}"
        )
        token = result["token"]

        with CreatedModelServiceTokenContext.with_current(token):
            yield
