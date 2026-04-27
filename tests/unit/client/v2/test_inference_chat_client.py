from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import aiohttp
import pytest
from aiohttp import web

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.v2.domains_v2.inference_chat import (
    InferenceChatAuthError,
    InferenceChatClient,
)

HandlerFn = Callable[[web.Request], Awaitable[web.StreamResponse]]


class _FakeServer:
    def __init__(self, runner: web.AppRunner, port: int, recorded: dict[str, Any]) -> None:
        self._runner = runner
        self.port = port
        self.recorded = recorded

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    async def stop(self) -> None:
        await self._runner.cleanup()


async def _start_server(
    method: str,
    path: str,
    handler: HandlerFn,
) -> _FakeServer:
    recorded: dict[str, Any] = {}
    app = web.Application()

    async def wrapped(request: web.Request) -> web.StreamResponse:
        recorded["method"] = request.method
        recorded["path"] = request.path
        recorded["headers"] = dict(request.headers)
        if request.can_read_body:
            recorded["json"] = await request.json()
        return await handler(request)

    app.router.add_route(method, path, wrapped)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    server_obj = site._server
    assert server_obj is not None
    sockets = server_obj.sockets
    assert sockets
    port = sockets[0].getsockname()[1]
    return _FakeServer(runner, port, recorded)


@pytest.fixture
async def chat_client() -> AsyncIterator[InferenceChatClient]:
    client = InferenceChatClient()
    try:
        yield client
    finally:
        await client.close()


def _request_body() -> dict[str, Any]:
    return {
        "model": "meta/test-model",
        "messages": [{"role": "user", "content": "hello"}],
    }


class TestChatCompletionSuccess:
    async def test_posts_to_v1_chat_completions_with_bearer_header(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({
                "id": "cmpl-1",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hi"},
                        "finish_reason": "stop",
                    }
                ],
            })

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            resp = await chat_client.chat_completion(
                server.base_url,
                "sk-test-token",
                _request_body(),
            )
        finally:
            await server.stop()

        assert server.recorded["method"] == "POST"
        assert server.recorded["path"] == "/v1/chat/completions"
        assert server.recorded["headers"]["Authorization"] == "Bearer sk-test-token"
        assert server.recorded["headers"]["Content-Type"] == "application/json"
        assert server.recorded["json"] == _request_body()
        assert resp["choices"][0]["message"]["content"] == "hi"

    async def test_endpoint_url_already_ending_in_chat_completions(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({"choices": []})

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            full_url = f"{server.base_url}/v1/chat/completions"
            await chat_client.chat_completion(full_url, "sk-x", _request_body())
        finally:
            await server.stop()
        assert server.recorded["path"] == "/v1/chat/completions"

    async def test_endpoint_url_with_trailing_slash_is_normalized(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({"choices": []})

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            full_url = f"{server.base_url}/v1/chat/completions/"
            await chat_client.chat_completion(full_url, "sk-x", _request_body())
        finally:
            await server.stop()
        assert server.recorded["path"] == "/v1/chat/completions"

    async def test_omits_authorization_when_api_key_is_none(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({"choices": []})

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            await chat_client.chat_completion(server.base_url, None, _request_body())
        finally:
            await server.stop()
        assert "Authorization" not in server.recorded["headers"]


class TestListModels:
    async def test_returns_models_payload(self, chat_client: InferenceChatClient) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({
                "object": "list",
                "data": [{"id": "qwen2.5-0.5b-instruct", "object": "model"}],
            })

        server = await _start_server("GET", "/v1/models", handler)
        try:
            payload = await chat_client.list_models(server.base_url, "sk-x")
        finally:
            await server.stop()
        assert server.recorded["path"] == "/v1/models"
        assert payload["data"][0]["id"] == "qwen2.5-0.5b-instruct"


class TestAuthErrors:
    async def test_401_raises_InferenceChatAuthError(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({"error": "invalid api key"}, status=401)

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            with pytest.raises(InferenceChatAuthError) as exc_info:
                await chat_client.chat_completion(server.base_url, "bad", _request_body())
        finally:
            await server.stop()
        assert exc_info.value.status == 401

    async def test_403_raises_InferenceChatAuthError(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({"error": "forbidden"}, status=403)

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            with pytest.raises(InferenceChatAuthError):
                await chat_client.chat_completion(server.base_url, "bad", _request_body())
        finally:
            await server.stop()


class TestServerErrors:
    async def test_500_raises_BackendAPIError_not_auth(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.json_response({"error": "boom"}, status=500)

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            with pytest.raises(BackendAPIError) as exc_info:
                await chat_client.chat_completion(server.base_url, "sk", _request_body())
        finally:
            await server.stop()
        assert not isinstance(exc_info.value, InferenceChatAuthError)
        assert exc_info.value.status == 500


class TestNonJsonResponse:
    async def test_non_json_response_raises_client_error(
        self, chat_client: InferenceChatClient
    ) -> None:
        async def handler(_request: web.Request) -> web.Response:
            return web.Response(text="not-json", content_type="text/plain")

        server = await _start_server("POST", "/v1/chat/completions", handler)
        try:
            with pytest.raises(BackendClientError):
                await chat_client.chat_completion(server.base_url, "sk", _request_body())
        finally:
            await server.stop()


class TestExternalSession:
    async def test_does_not_close_externally_owned_session(self) -> None:
        async with aiohttp.ClientSession() as external:
            client = InferenceChatClient(session=external)
            await client.close()
            assert external.closed is False
