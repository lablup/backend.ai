"""SDK client for OpenAI Chat Completions deployment endpoints.

:class:`DeploymentChatClient` targets endpoints that follow the OpenAI HTTP
contract (``POST /v1/chat/completions`` with an ``{model, messages, ...}``
JSON body): vLLM, SGLang, NVIDIA NIM, and TGI in Messages API mode. Vanilla
TGI's native ``/generate`` and arbitrary custom containers are out of scope.

Session lifecycle, JSON parsing, URL normalization, and 401/403 → auth-error
mapping live on :class:`BackendAIAppProxyClient` in
:mod:`ai.backend.client.v2.base_client`.
"""

from __future__ import annotations

from typing import Any

from ai.backend.client.v2.base_client import BackendAIAppProxyClient

_OPENAI_COMPATIBLE_CHAT_PATH = "/v1/chat/completions"


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
    ) -> dict[str, Any]:
        return await self._request(
            "POST", endpoint_url, _OPENAI_COMPATIBLE_CHAT_PATH, token, body=body
        )
