from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from uuid import UUID, uuid4

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from ai.backend.manager.clients.appproxy.client import AppProxyClient
from ai.backend.manager.clients.appproxy.types import (
    CreateSessionAppTokenRequestBody,
    SessionAppSessionInfo,
)
from ai.backend.manager.errors.appproxy import AppProxyResponseError

_API_TOKEN = "coordinator-api-secret"

type ConfHandler = Callable[[web.Request], Coroutine[Any, Any, web.Response]]
type ClientFactory = Callable[[ConfHandler], Coroutine[Any, Any, AppProxyClient]]


@pytest.fixture
async def client_factory(aiohttp_server: Any) -> AsyncIterator[ClientFactory]:
    sessions: list[ClientSession] = []

    async def _factory(handler: ConfHandler) -> AppProxyClient:
        app = web.Application()
        app.router.add_post("/v2/conf", handler)
        server: TestServer = await aiohttp_server(app)
        address = str(server.make_url("/"))
        session = ClientSession(base_url=address)
        sessions.append(session)
        return AppProxyClient(session, address, _API_TOKEN)

    try:
        yield _factory
    finally:
        for session in sessions:
            await session.close()


def _make_body(session_id: UUID) -> CreateSessionAppTokenRequestBody:
    return CreateSessionAppTokenRequestBody(
        login_session_token=None,
        kernel_host="10.0.0.5",
        kernel_port=30080,
        session=SessionAppSessionInfo(
            id=session_id,
            user_uuid=uuid4(),
            group_id=uuid4(),
            access_key="AKIATEST",
            domain_name="default",
        ),
    )


class TestCreateSessionAppToken:
    async def test_sends_api_token_and_returns_issued_token(
        self, client_factory: ClientFactory
    ) -> None:
        received: dict[str, Any] = {}

        async def handler(request: web.Request) -> web.Response:
            received["token_header"] = request.headers.get("X-BackendAI-Token")
            received["body"] = await request.json()
            return web.json_response({"token": "issued-token"})

        client = await client_factory(handler)
        session_id = uuid4()

        token = await client.create_session_app_token(_make_body(session_id))

        assert token == "issued-token"
        assert received["token_header"] == _API_TOKEN
        assert received["body"]["kernel_host"] == "10.0.0.5"
        assert received["body"]["kernel_port"] == 30080
        assert received["body"]["session"]["id"] == str(session_id)
        assert "group_id" in received["body"]["session"]

    async def test_raises_when_response_has_no_token(self, client_factory: ClientFactory) -> None:
        async def handler(request: web.Request) -> web.Response:
            return web.json_response({"unexpected": True})

        client = await client_factory(handler)

        with pytest.raises(AppProxyResponseError):
            await client.create_session_app_token(_make_body(uuid4()))
