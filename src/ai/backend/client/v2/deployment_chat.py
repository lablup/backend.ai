"""SDK client for OpenAI Chat Completions deployment endpoints.

:class:`DeploymentChatClient` targets endpoints that follow the OpenAI HTTP
contract (``POST /v1/chat/completions`` with an ``{model, messages, ...}``
JSON body): vLLM, SGLang, NVIDIA NIM, and TGI in Messages API mode. Vanilla
TGI's native ``/generate`` and arbitrary custom containers are out of scope.

Wire DTOs (``ChatCompletionRequest``, ``ListModelsResponse``, etc.) live in
:mod:`ai.backend.common.dto.clients.openai_compat` so other components can
reuse them. Session lifecycle, JSON parsing, URL normalization, and
401/403 → auth-error mapping live on :class:`BackendAIAppProxyClient` in
:mod:`ai.backend.client.v2.base_client`.
"""

from __future__ import annotations

from typing import Any

from ai.backend.client.v2.base_client import BackendAIAppProxyClient
from ai.backend.common.dto.clients.openai_compat import (
    ChatCompletionResponse,
    ListModelsResponse,
)

_OPENAI_COMPATIBLE_CHAT_PATH = "/v1/chat/completions"
_OPENAI_COMPATIBLE_MODELS_PATH = "/v1/models"


class DeploymentChatClient(BackendAIAppProxyClient):
    """OpenAI Chat Completions client for direct-to-deployment inference traffic.

    Sends ``POST /v1/chat/completions`` with an OpenAI-shaped
    ``{model, messages, ...}`` JSON body. Compatible runtimes: vLLM,
    SGLang, NVIDIA NIM, and TGI in Messages API mode. Vanilla TGI
    (``/generate``) and arbitrary custom containers need a different
    :class:`BackendAIAppProxyClient` subclass.
    """

    async def chat_completion(
        self,
        endpoint_url: str,
        token: str | None,
        body: dict[str, Any],
    ) -> ChatCompletionResponse:
        payload = await self._request(
            "POST", endpoint_url, _OPENAI_COMPATIBLE_CHAT_PATH, token, body=body
        )
        return ChatCompletionResponse.model_validate(payload)

    async def list_models(
        self,
        endpoint_url: str,
        token: str | None,
    ) -> ListModelsResponse:
        """Fetch ``GET /v1/models`` — the OpenAI-compat model listing.

        Used to auto-derive a default model name when the caller did not
        pass ``--model`` and no cached default is known.
        """
        payload = await self._request("GET", endpoint_url, _OPENAI_COMPATIBLE_MODELS_PATH, token)
        return ListModelsResponse.model_validate(payload)
