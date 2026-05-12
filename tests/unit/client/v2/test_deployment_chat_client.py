from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from aioresponses import aioresponses
from pydantic import ValidationError
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.deployment_chat import DeploymentChatClient
from ai.backend.client.v2.exceptions import DeploymentAuthError
from ai.backend.common.dto.clients.openai_compat import ChatCompletionResponse
from ai.backend.common.exception import BackendAISchemaValidationFailed

BASE_URL = "http://infer.test.local"
CHAT_URL = f"{BASE_URL}/v1/chat/completions"


@pytest.fixture
async def chat_client() -> AsyncIterator[DeploymentChatClient]:
    # ``endpoint`` is required on ClientConfig but unused by AppProxyClient.
    config = ClientConfig(endpoint=URL("http://manager.unused"))
    client = DeploymentChatClient(config)
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
        assert isinstance(resp, ChatCompletionResponse)
        assert resp.choices[0].message.content == "hi"
        assert resp.assistant_message == "hi"

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


class TestAuthErrors:
    async def test_401_raises_DeploymentAuthError(self, chat_client: DeploymentChatClient) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, status=401, payload={"error": "invalid api key"})
            with pytest.raises(DeploymentAuthError) as exc_info:
                await chat_client.chat_completion(BASE_URL, "bad", _make_body())
        assert exc_info.value.status == 401

    async def test_403_raises_DeploymentAuthError(self, chat_client: DeploymentChatClient) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, status=403, payload={"error": "forbidden"})
            with pytest.raises(DeploymentAuthError):
                await chat_client.chat_completion(BASE_URL, "bad", _make_body())


class TestServerErrors:
    async def test_500_raises_BackendAPIError_not_auth(
        self, chat_client: DeploymentChatClient
    ) -> None:
        with aioresponses() as m:
            m.post(CHAT_URL, status=500, payload={"error": "boom"})
            with pytest.raises(BackendAPIError) as exc_info:
                await chat_client.chat_completion(BASE_URL, "sk", _make_body())
        assert not isinstance(exc_info.value, DeploymentAuthError)
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


class TestChatCompletionResponseModel:
    """Direct coverage for the response Pydantic model.

    ``DeploymentChatClient.chat_completion`` runs ``model_validate`` on the
    payload, so failures here surface as ``ValidationError`` at the SDK
    boundary instead of corrupting persisted chat history downstream.
    """

    def test_assistant_message_returns_first_choice_text(self) -> None:
        resp = ChatCompletionResponse.model_validate({
            "choices": [
                {"message": {"role": "assistant", "content": "hi 길동"}},
                {"message": {"role": "assistant", "content": "ignored"}},
            ],
        })
        assert resp.assistant_message == "hi 길동"

    def test_assistant_message_none_when_choices_empty(self) -> None:
        # vLLM emits choices=[] on certain error paths; the CLI uses this
        # to skip half-recorded history rounds.
        resp = ChatCompletionResponse.model_validate({"choices": []})
        assert resp.assistant_message is None

    def test_assistant_message_none_for_tool_call_only_response(self) -> None:
        # Function-calling responses leave message.content as null and put
        # the call in tool_calls; nothing text-shaped to persist.
        resp = ChatCompletionResponse.model_validate({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "lookup", "arguments": "{}"},
                            },
                        ],
                    },
                },
            ],
        })
        assert resp.assistant_message is None

    def test_extra_top_level_fields_round_trip(self) -> None:
        # Runtime-specific telemetry (usage, system_fingerprint, vLLM
        # prompt_logprobs, NIM extras) must survive parsing so the CLI's
        # JSON pretty-print still shows them to the user.
        payload: dict[str, Any] = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 1741569952,
            "model": "vllm/test",
            "choices": [{"message": {"role": "assistant", "content": "hi"}}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 1, "total_tokens": 5},
            "system_fingerprint": "fp_xyz",
        }
        resp = ChatCompletionResponse.model_validate(payload)
        dumped = resp.model_dump(mode="json")
        assert dumped["usage"]["total_tokens"] == 5
        assert dumped["system_fingerprint"] == "fp_xyz"
        assert dumped["model"] == "vllm/test"

    def test_streaming_chunk_shape_fails_validation(self) -> None:
        # ``delta`` is the streaming-chunk shape; the SDK never sets
        # stream=true, so its arrival means the server misbehaved.
        # Failing loudly is preferable to silently dropping the round.
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ChatCompletionResponse.model_validate({
                "choices": [
                    {"delta": {"role": "assistant", "content": "partial"}},
                ],
            })
