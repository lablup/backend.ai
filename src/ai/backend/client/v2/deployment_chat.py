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

from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import aiohttp
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError, BackendClientError

DEFAULT_CHAT_PATH = "/v1/chat/completions"
DEFAULT_MODELS_PATH = "/v1/models"


class DeploymentChatAuthError(BackendAPIError):
    """Raised when the inference endpoint rejects the configured API key."""


@dataclass(frozen=True)
class DeploymentChatClientArgs:
    """Connection knobs for :meth:`DeploymentChatClient.create`."""

    skip_ssl_verification: bool = False
    connect_timeout: float | None = 10.0
    read_timeout: float | None = 300.0


class DeploymentChatClient:
    """Direct HTTP client for OpenAI-compatible inference endpoints."""

    _session: aiohttp.ClientSession

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    @classmethod
    async def create(cls, args: DeploymentChatClientArgs) -> Self:
        connector = aiohttp.TCPConnector(ssl=not args.skip_ssl_verification)
        timeout = aiohttp.ClientTimeout(
            sock_connect=args.connect_timeout,
            sock_read=args.read_timeout,
        )
        session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return cls(session)

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
        if not self._session.closed:
            await self._session.close()

    async def chat_completion(
        self,
        endpoint_url: str,
        api_key: str | None,
        body: dict[str, Any],
        *,
        path: str = DEFAULT_CHAT_PATH,
    ) -> dict[str, Any]:
        """POST a chat completion request to the deployment endpoint."""
        target = self._build_url(endpoint_url, path)
        return await self._post(target, api_key, body)

    async def list_models(
        self,
        endpoint_url: str,
        api_key: str | None,
        *,
        path: str = DEFAULT_MODELS_PATH,
    ) -> dict[str, Any]:
        """GET the list of models served by the deployment endpoint."""
        target = self._build_url(endpoint_url, path)
        return await self._get(target, api_key)

    async def _post(
        self,
        target: str,
        api_key: str | None,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        headers = self._auth_headers(api_key, json_body=True)
        try:
            async with self._session.post(target, headers=headers, json=body) as resp:
                payload = await self._read_payload(resp)
                self._raise_for_status(resp, payload)
        except aiohttp.ClientConnectionError as e:
            raise BackendClientError(f"failed to reach inference endpoint: {e!r}") from e
        return self._ensure_dict(payload)

    async def _get(
        self,
        target: str,
        api_key: str | None,
    ) -> dict[str, Any]:
        headers = self._auth_headers(api_key, json_body=False)
        try:
            async with self._session.get(target, headers=headers) as resp:
                payload = await self._read_payload(resp)
                self._raise_for_status(resp, payload)
        except aiohttp.ClientConnectionError as e:
            raise BackendClientError(f"failed to reach inference endpoint: {e!r}") from e
        return self._ensure_dict(payload)

    @staticmethod
    def _auth_headers(api_key: str | None, *, json_body: bool) -> dict[str, str]:
        headers: dict[str, str] = {}
        if json_body:
            headers["Content-Type"] = "application/json"
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    @staticmethod
    def _build_url(endpoint_url: str, path: str) -> str:
        base = URL(endpoint_url)
        target_path = path if path.startswith("/") else "/" + path
        base_path = base.path.rstrip("/")
        if base_path.endswith(target_path):
            return str(base.with_path(base_path))
        return str(base.with_path(f"{base_path}{target_path}"))

    @staticmethod
    def _raise_for_status(resp: aiohttp.ClientResponse, payload: object) -> None:
        if resp.status < 400:
            return
        data = payload if isinstance(payload, dict) else {"detail": payload}
        if resp.status in (401, 403):
            raise DeploymentChatAuthError(resp.status, resp.reason or "Unauthorized", data)
        raise BackendAPIError(resp.status, resp.reason or "HTTP error", data)

    @staticmethod
    def _ensure_dict(payload: object) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise BackendClientError(f"inference endpoint returned non-JSON response: {payload!r}")
        return payload

    @staticmethod
    async def _read_payload(resp: aiohttp.ClientResponse) -> object:
        try:
            return await resp.json()
        except (aiohttp.ContentTypeError, ValueError):
            return await resp.text()
