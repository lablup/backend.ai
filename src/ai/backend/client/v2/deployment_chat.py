"""SDK client for OpenAI-compatible inference endpoints (vLLM, TGI, SGLang, NIM).

Talks **directly** to a deployment's inference endpoint, not the Backend.AI
manager. Manages its own ``aiohttp`` session and uses ``Authorization: Bearer``
auth (or no auth) per the OpenAI HTTP contract.

Request and response payloads are passed as plain ``dict[str, Any]`` so that
the SDK does not have to track every runtime variant's extension fields. The
caller is responsible for assembling an OpenAI-shaped request body and
interpreting the response.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import aiohttp
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.v2.exceptions import DeploymentChatAuthError

DEFAULT_CHAT_PATH = "/v1/chat/completions"
DEFAULT_MODELS_PATH = "/v1/models"

DEFAULT_CONNECT_TIMEOUT_SEC: float = 10.0
"""TCP connect timeout for inference-endpoint calls."""

DEFAULT_READ_TIMEOUT_SEC: float = 300.0
"""Per-socket read timeout — generous because chat-completion responses
can take minutes for long-form generations."""


@dataclass(frozen=True)
class DeploymentChatClientArgs:
    """Connection knobs for :class:`DeploymentChatClient`."""

    skip_ssl_verification: bool = False
    connect_timeout: float | None = DEFAULT_CONNECT_TIMEOUT_SEC
    read_timeout: float | None = DEFAULT_READ_TIMEOUT_SEC


class DeploymentChatClient:
    """Direct HTTP client for OpenAI-compatible inference endpoints."""

    _session: aiohttp.ClientSession

    def __init__(self, args: DeploymentChatClientArgs) -> None:
        connector = aiohttp.TCPConnector(ssl=not args.skip_ssl_verification)
        timeout = aiohttp.ClientTimeout(
            sock_connect=args.connect_timeout,
            sock_read=args.read_timeout,
        )
        self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def chat_completion(
        self,
        endpoint_url: str,
        token: str | None,
        body: dict[str, Any],
        *,
        path: str = DEFAULT_CHAT_PATH,
    ) -> dict[str, Any]:
        """POST a chat completion request to the deployment endpoint."""
        return await self._request("POST", endpoint_url, path, token, body=body)

    async def list_models(
        self,
        endpoint_url: str,
        token: str | None,
        *,
        path: str = DEFAULT_MODELS_PATH,
    ) -> dict[str, Any]:
        """GET the list of models served by the deployment endpoint."""
        return await self._request("GET", endpoint_url, path, token)

    async def _request(
        self,
        method: str,
        endpoint_url: str,
        path: str,
        token: str | None,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        target = self._build_url(endpoint_url, path)
        headers: dict[str, str] = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with self._session.request(method, target, headers=headers, json=body) as resp:
                # Backend.AI's app-proxy fronts every deployment endpoint, and on
                # 5xx it can emit HTML / plain-text bodies (e.g. cloud LB error
                # pages) instead of JSON. Read text up front so the raw body is
                # available either as the JSON-parse input or as context in the
                # raised error.
                raw = await resp.text()
                try:
                    payload = json.loads(raw) if raw else None
                except json.JSONDecodeError as e:
                    if resp.status >= 400:
                        raise BackendAPIError(
                            resp.status, resp.reason or "HTTP error", {"detail": raw}
                        ) from e
                    raise BackendClientError(
                        f"inference endpoint returned non-JSON response "
                        f"(status={resp.status}): {raw!r}"
                    ) from e
                if not isinstance(payload, dict):
                    raise BackendClientError(
                        f"inference endpoint returned non-object payload "
                        f"(type={type(payload).__name__}, status={resp.status}): {payload!r}"
                    )
                self._raise_for_status(resp, payload)
                return payload
        except aiohttp.ClientConnectionError as e:
            raise BackendClientError(f"failed to reach inference endpoint: {e!r}") from e

    @staticmethod
    def _build_url(endpoint_url: str, path: str) -> str:
        base = URL(endpoint_url)
        target_path = path if path.startswith("/") else "/" + path
        base_path = base.path.rstrip("/")
        if base_path.endswith(target_path):
            return str(base.with_path(base_path))
        return str(base.with_path(f"{base_path}{target_path}"))

    @staticmethod
    def _raise_for_status(resp: aiohttp.ClientResponse, payload: dict[str, Any]) -> None:
        if resp.status < 400:
            return
        if resp.status in (401, 403):
            raise DeploymentChatAuthError(resp.status, resp.reason or "Unauthorized", payload)
        raise BackendAPIError(resp.status, resp.reason or "HTTP error", payload)
