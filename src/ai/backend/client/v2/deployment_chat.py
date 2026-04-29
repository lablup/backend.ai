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

from pydantic import BaseModel, ConfigDict

from ai.backend.client.v2.base_client import BackendAIAppProxyClient

_OPENAI_COMPATIBLE_CHAT_PATH = "/v1/chat/completions"
_OPENAI_COMPATIBLE_MODELS_PATH = "/v1/models"


class ModelEntry(BaseModel):
    """One entry in an OpenAI-compat ``GET /v1/models`` response.

    Runtimes (vLLM, SGLang, NIM) typically include extra fields such as
    ``created`` or ``owned_by``; ``extra="allow"`` keeps them on the
    model so future additions don't break parsing.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "model"


class ListModelsResponse(BaseModel):
    """Body of ``GET /v1/models`` on an OpenAI-compat endpoint."""

    model_config = ConfigDict(extra="allow")

    object: str = "list"
    data: list[ModelEntry]


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
