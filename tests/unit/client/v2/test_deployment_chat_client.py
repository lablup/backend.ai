from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from aioresponses import aioresponses
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.v2.deployment_chat import (
    DeploymentChatClient,
    DeploymentChatClientArgs,
)
from ai.backend.client.v2.exceptions import DeploymentChatAuthError

BASE_URL = "http://infer.test.local"
CHAT_URL = f"{BASE_URL}/v1/chat/completions"
MODELS_URL = f"{BASE_URL}/v1/models"


@pytest.fixture
async def chat_client() -> AsyncIterator[DeploymentChatClient]:
    client = DeploymentChatClient(DeploymentChatClientArgs())
    try:
        yield client
    finally:
        await client.close()


def _make_body() -> dict[str, Any]:
    return {
        "model": "meta/test-model",
        "messages": [{"role": "user", "content": "hello"}],
    }


def _last_call(mock: aioresponses, method: str, url: str) -> Any:
    """Return the most recent ``RequestCall`` aioresponses captured for (method, url)."""
    key = (method.upper(), URL(url))
    calls = mock.requests[key]
    assert calls, f"no request was captured for {method} {url}"
    return calls[-1]


class TestChatCompletionSuccess:
    async def test_posts_to_v1_chat_completions_with_bearer_header(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(
                CHAT_URL,
                payload={
                    "id": "cmpl-1",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "hi"},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )
            resp = await chat_client.chat_completion(BASE_URL, "sk-test-token", _make_body())
            call = _last_call(m, "POST", CHAT_URL)

        assert call.kwargs["headers"]["Authorization"] == "Bearer sk-test-token"
        assert call.kwargs["headers"]["Content-Type"] == "application/json"
        assert call.kwargs["json"] == _make_body()
        assert resp["choices"][0]["message"]["content"] == "hi"

    async def test_endpoint_url_already_ending_in_chat_completions(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, payload={"choices": []})
            await chat_client.chat_completion(CHAT_URL, "sk-x", _make_body())
            assert (("POST", URL(CHAT_URL))) in m.requests

    async def test_endpoint_url_with_trailing_slash_is_normalized(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, payload={"choices": []})
            await chat_client.chat_completion(f"{CHAT_URL}/", "sk-x", _make_body())
            assert (("POST", URL(CHAT_URL))) in m.requests

    async def test_omits_authorization_when_token_is_none(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, payload={"choices": []})
            await chat_client.chat_completion(BASE_URL, None, _make_body())
            call = _last_call(m, "POST", CHAT_URL)
        assert "Authorization" not in call.kwargs["headers"]


class TestListModels:
    async def test_returns_models_payload(self, chat_client: DeploymentChatClient) -> None:
        with aioresponses() as m:
            m.get(
                MODELS_URL,
                payload={
                    "object": "list",
                    "data": [{"id": "qwen2.5-0.5b-instruct", "object": "model"}],
                },
            )
            payload = await chat_client.list_models(BASE_URL, "sk-x")
        assert payload["data"][0]["id"] == "qwen2.5-0.5b-instruct"


class TestAuthErrors:
    async def test_401_raises_DeploymentChatAuthError(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, status=401, payload={"error": "invalid api key"})
            with pytest.raises(DeploymentChatAuthError) as exc_info:
                await chat_client.chat_completion(BASE_URL, "bad", _make_body())
        assert exc_info.value.status == 401

    async def test_403_raises_DeploymentChatAuthError(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, status=403, payload={"error": "forbidden"})
            with pytest.raises(DeploymentChatAuthError):
                await chat_client.chat_completion(BASE_URL, "bad", _make_body())


class TestServerErrors:
    async def test_500_raises_BackendAPIError_not_auth(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, status=500, payload={"error": "boom"})
            with pytest.raises(BackendAPIError) as exc_info:
                await chat_client.chat_completion(BASE_URL, "sk", _make_body())
        assert not isinstance(exc_info.value, DeploymentChatAuthError)
        assert exc_info.value.status == 500


class TestNonJsonResponse:
    async def test_non_json_2xx_raises_client_error(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, status=200, body="not-json", content_type="text/plain")
            with pytest.raises(BackendClientError):
                await chat_client.chat_completion(BASE_URL, "sk", _make_body())

    async def test_html_5xx_raises_backend_api_error_with_body(
        self, chat_client: DeploymentChatClient
    ) -> None:
        # app-proxy / cloud LB error pages: 5xx with HTML body. The HTTP
        # status carries the meaningful failure signal, so this surfaces as
        # BackendAPIError with the raw body in ``detail``.
        with aioresponses() as m:
            m.post(
                CHAT_URL,
                status=502,
                body="<html><body>Bad Gateway</body></html>",
                content_type="text/html",
            )
            with pytest.raises(BackendAPIError) as exc_info:
                await chat_client.chat_completion(BASE_URL, "sk", _make_body())
        assert exc_info.value.status == 502
        assert "Bad Gateway" in exc_info.value.data["detail"]
