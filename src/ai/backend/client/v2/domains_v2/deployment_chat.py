"""SDK client for OpenAI-compatible chat against deployed vLLM endpoints.

Unlike the other ``domains_v2`` clients, this one talks **directly** to the
deployment's inference endpoint (the vLLM container) using the API key the
user configured at deployment time, not the Backend.AI manager. It therefore
manages its own ``aiohttp`` session and uses ``Authorization: Bearer`` rather
than the HMAC signature applied by ``BackendAIAuthClient``.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

import aiohttp
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.v2.chat_dto import ChatCompletionRequest, ChatCompletionResponse


class DeploymentChatAuthError(BackendAPIError):
    """Raised when the inference endpoint rejects the configured API key."""


class DeploymentChatClient:
    """Direct HTTP client for OpenAI-compatible chat completions on vLLM."""

    _session: aiohttp.ClientSession
    _owns_session: bool

    def __init__(
        self,
        *,
        session: aiohttp.ClientSession | None = None,
        skip_ssl_verification: bool = False,
    ) -> None:
        if session is not None:
            self._session = session
            self._owns_session = False
        else:
            connector = aiohttp.TCPConnector(ssl=not skip_ssl_verification)
            self._session = aiohttp.ClientSession(connector=connector)
            self._owns_session = True

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_session and not self._session.closed:
            await self._session.close()

    async def chat_completion(
        self,
        endpoint_url: str,
        api_key: str | None,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """POST a chat completion request to the deployment endpoint.

        ``endpoint_url`` is the deployment's base URL as returned by
        ``deployment.get(...).network_access.endpoint_url``. ``api_key``
        corresponds to the value vLLM was started with (``--api-key``);
        pass ``None`` for deployments that disabled API-key authentication.
        """
        target = self._build_chat_url(endpoint_url)
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        body = request.model_dump(mode="json", exclude_none=True)
        try:
            async with self._session.post(target, headers=headers, json=body) as resp:
                payload = await self._read_payload(resp)
                if resp.status in (401, 403):
                    raise DeploymentChatAuthError(
                        resp.status,
                        resp.reason or "Unauthorized",
                        payload if isinstance(payload, dict) else {"detail": payload},
                    )
                if resp.status >= 400:
                    raise BackendAPIError(
                        resp.status,
                        resp.reason or "HTTP error",
                        payload if isinstance(payload, dict) else {"detail": payload},
                    )
        except aiohttp.ClientConnectionError as e:
            raise BackendClientError(f"failed to reach inference endpoint: {e!r}") from e
        if not isinstance(payload, dict):
            raise BackendClientError(f"inference endpoint returned non-JSON response: {payload!r}")
        parsed = ChatCompletionResponse.model_validate(payload)
        if parsed.raw is None:
            parsed = parsed.model_copy(update={"raw": payload})
        return parsed

    @staticmethod
    def _build_chat_url(endpoint_url: str) -> str:
        base = URL(endpoint_url)
        path = base.path.rstrip("/")
        if path.endswith("/v1/chat/completions"):
            return str(base)
        return str(base.with_path(f"{path}/v1/chat/completions"))

    @staticmethod
    async def _read_payload(resp: aiohttp.ClientResponse) -> object:
        try:
            return await resp.json()
        except (aiohttp.ContentTypeError, ValueError):
            return await resp.text()
