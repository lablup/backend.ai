from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable, Mapping
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self, TypeVar, cast

import aiohttp
from multidict import CIMultiDict
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.common.api_handlers import (
    BaseRequestModel,
    BaseResponseModel,
    BaseRootResponseModel,
)

from .auth import AuthStrategy
from .config import ClientConfig
from .exceptions import (
    DeploymentAuthError,
    SSEError,
    WebSocketError,
    map_status_to_exception,
)
from .streaming_types import SSEConnection, WebSocketSession

ResponseT = TypeVar("ResponseT", bound=BaseResponseModel | BaseRootResponseModel[Any])


def _create_aiohttp_session(config: ClientConfig) -> aiohttp.ClientSession:
    ssl_context: bool = not config.skip_ssl_verification
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(
        sock_connect=config.connection_timeout or None,
        sock_read=config.read_timeout or None,
    )
    cookie_jar = config.cookie_jar
    if cookie_jar is None and config.endpoint_type == "session":
        cookie_jar = aiohttp.CookieJar(unsafe=True)
    if cookie_jar is not None:
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            cookie_jar=cookie_jar,
        )
    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
    )


class BackendAIAuthClient:
    """Async HTTP client for Backend.AI REST API.

    All public request methods accept and return Pydantic models only.
    Use ``typed_request()`` as the sole public interface for making API calls.

    Prefer ``create()`` for production use; ``__init__`` accepts a pre-built
    session so tests can inject a mock directly.
    """

    _config: ClientConfig
    _auth: AuthStrategy
    _session: aiohttp.ClientSession

    def __init__(
        self,
        config: ClientConfig,
        auth: AuthStrategy,
        session: aiohttp.ClientSession,
    ) -> None:
        self._config = config
        self._auth = auth
        self._session = session

    @classmethod
    async def create(
        cls,
        config: ClientConfig,
        auth: AuthStrategy,
    ) -> BackendAIAuthClient:
        session = _create_aiohttp_session(config)
        return cls(config, auth, session)

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    @property
    def config(self) -> ClientConfig:
        return self._config

    async def close(self) -> None:
        await self._session.close()

    def _build_url(self, path: str) -> str:
        base = str(self._config.endpoint).rstrip("/")
        path = path.lstrip("/")
        if self._config.endpoint_type == "session":
            return f"{base}/func/{path}"
        return f"{base}/{path}"

    def build_url_raw(self, path: str) -> str:
        """Build URL without /func/ prefix (for webserver-native endpoints like /server/login)."""
        base = str(self._config.endpoint).rstrip("/")
        return f"{base}/{path.lstrip('/')}"

    def _sign(self, method: str, rel_url: str, content_type: str) -> Mapping[str, str]:
        now = datetime.now(UTC)
        headers = self._auth.sign(
            method=method,
            version=self._config.api_version,
            endpoint=self._config.endpoint,
            date=now,
            rel_url=rel_url,
            content_type=content_type,
        )
        return {
            "Date": now.isoformat(),
            "Content-Type": content_type,
            "X-BackendAI-Version": self._config.api_version,
            **headers,
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, str] | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | str | None:
        session = self._session
        content_type = "application/json"
        rel_url = "/" + path.lstrip("/")
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            rel_url = f"{rel_url}?{qs}"
        headers = {**self._sign(method, rel_url, content_type)}
        if extra_headers:
            headers.update(extra_headers)
        url = self._build_url(path)
        async with session.request(
            method,
            url,
            headers=headers,
            json=json,
            params=params,
        ) as resp:
            if resp.status >= 400:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", data)
            if resp.status == 204:
                return None
            result: dict[str, Any] | list[Any] | str = await resp.json()
            return result

    async def typed_request(
        self,
        method: str,
        path: str,
        *,
        request: BaseRequestModel | None = None,
        response_model: type[ResponseT],
        params: dict[str, str] | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> ResponseT:
        json_body = (
            request.model_dump(mode="json", exclude_none=True, exclude_unset=True)
            if request is not None
            else None
        )
        data = await self._request(
            method, path, json=json_body, params=params, extra_headers=extra_headers
        )
        if data is None:
            raise BackendAPIError(
                204,
                "No Content",
                {
                    "type": "https://api.backend.ai/probs/unexpected-no-content",
                    "title": f"Expected a JSON response from {method} {path}, but got 204 No Content",
                },
            )
        return cast(ResponseT, response_model.model_validate(data))

    async def typed_request_no_content(
        self,
        method: str,
        path: str,
        *,
        request: BaseRequestModel | None = None,
        params: dict[str, str] | None = None,
    ) -> None:
        json_body = (
            request.model_dump(mode="json", exclude_none=True, exclude_unset=True)
            if request is not None
            else None
        )
        await self._request(method, path, json=json_body, params=params)

    async def upload(
        self,
        path: str,
        data: aiohttp.FormData,
        *,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """Send a multipart file upload and return the parsed JSON response."""
        session = self._session
        rel_url = "/" + path.lstrip("/")
        headers = dict(self._sign("POST", rel_url, "multipart/form-data"))
        # Let aiohttp set the actual Content-Type with the multipart boundary.
        del headers["Content-Type"]
        url = self._build_url(path)
        async with session.request(
            "POST",
            url,
            headers=headers,
            data=data,
            params=params,
        ) as resp:
            if resp.status >= 400:
                try:
                    err_data = await resp.json()
                except Exception:
                    err_data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", err_data)
            if resp.status == 204:
                return None
            result: dict[str, Any] = await resp.json()
            return result

    async def download(
        self,
        path: str,
        *,
        method: str = "POST",
        json: Any | None = None,
        params: dict[str, str] | None = None,
    ) -> bytes:
        """Send a request and return the raw binary response."""
        session = self._session
        content_type = "application/json"
        rel_url = "/" + path.lstrip("/")
        headers = dict(self._sign(method, rel_url, content_type))
        url = self._build_url(path)
        async with session.request(
            method,
            url,
            headers=headers,
            json=json,
            params=params,
        ) as resp:
            if resp.status >= 400:
                try:
                    err_data = await resp.json()
                except Exception:
                    err_data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", err_data)
            return await resp.read()

    @asynccontextmanager
    async def ws_connect(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
        heartbeat: float | None = 30.0,
        protocols: Iterable[str] = (),
    ) -> AsyncIterator[WebSocketSession]:
        """Open a WebSocket connection with proper auth headers.

        Usage::

            async with client.ws_connect("/stream/session/abc/pty") as ws:
                await ws.send_str("hello")
                async for msg in ws:
                    print(msg.data)
        """
        rel_url = "/" + path.lstrip("/")
        headers = self._sign("GET", rel_url, "application/octet-stream")
        url = self._build_url(path)
        ws: aiohttp.ClientWebSocketResponse | None = None
        try:
            ws = await self._session.ws_connect(
                url,
                headers=headers,
                autoping=True,
                heartbeat=heartbeat,
                protocols=protocols,
                params=params,
            )
        except aiohttp.WSServerHandshakeError as e:
            raise map_status_to_exception(e.status, e.message or "", {"title": str(e)}) from e
        except aiohttp.ClientConnectionError as e:
            raise WebSocketError(f"WebSocket connection failed: {e!r}") from e
        session = WebSocketSession(ws)
        try:
            yield session
        finally:
            await session.close()

    @asynccontextmanager
    async def sse_connect(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> AsyncIterator[SSEConnection]:
        """Open an SSE connection with proper auth headers.

        Usage::

            async with client.sse_connect("/events/session") as events:
                async for event in events:
                    print(event.event, event.data)
        """
        rel_url = "/" + path.lstrip("/")
        headers = dict(self._sign("GET", rel_url, "text/event-stream"))
        headers["Accept"] = "text/event-stream"
        url = self._build_url(path)
        timeout = aiohttp.ClientTimeout(total=None, sock_read=None)
        resp: aiohttp.ClientResponse | None = None
        try:
            resp = await self._session.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
            )
        except aiohttp.ClientConnectionError as e:
            raise SSEError(f"SSE connection failed: {e!r}") from e
        try:
            if resp.status >= 400:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", data)
            connection = SSEConnection(resp)
            yield connection
        finally:
            if resp is not None:
                resp.close()


class BackendAIAnonymousClient:
    """Unauthenticated HTTP client for anonymous Backend.AI endpoints.

    Sends only ``Date``, ``Content-Type``, and ``X-BackendAI-Version``
    headers — no ``Authorization`` header is attached.

    Provides convenience methods for the three auth endpoints that do
    not require authentication: ``authorize``, ``signup``, and
    ``update_password_no_auth``.
    """

    _config: ClientConfig
    _session: aiohttp.ClientSession

    def __init__(
        self,
        config: ClientConfig,
        session: aiohttp.ClientSession,
    ) -> None:
        self._config = config
        self._session = session

    @classmethod
    async def create(
        cls,
        config: ClientConfig,
    ) -> BackendAIAnonymousClient:
        session = _create_aiohttp_session(config)
        return cls(config, session)

    async def close(self) -> None:
        await self._session.close()

    def _build_url(self, path: str) -> str:
        base = str(self._config.endpoint).rstrip("/")
        path = path.lstrip("/")
        if self._config.endpoint_type == "session":
            return f"{base}/func/{path}"
        return f"{base}/{path}"

    def _build_headers(self, method: str, rel_url: str, content_type: str) -> CIMultiDict[str]:
        return CIMultiDict({
            "Date": datetime.now(UTC).isoformat(),
            "Content-Type": content_type,
            "X-BackendAI-Version": self._config.api_version,
        })

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, str] | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | str | None:
        content_type = "application/json"
        rel_url = "/" + path.lstrip("/")
        headers = self._build_headers(method, rel_url, content_type)
        if extra_headers:
            headers.update(extra_headers)
        url = self._build_url(path)
        async with self._session.request(
            method,
            url,
            headers=headers,
            json=json,
            params=params,
        ) as resp:
            if resp.status >= 400:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", data)
            if resp.status == 204:
                return None
            result: dict[str, Any] | list[Any] | str = await resp.json()
            return result

    async def typed_request(
        self,
        method: str,
        path: str,
        *,
        request: BaseRequestModel | None = None,
        response_model: type[ResponseT],
        params: dict[str, str] | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> ResponseT:
        json_body = (
            request.model_dump(mode="json", exclude_none=True, exclude_unset=True)
            if request is not None
            else None
        )
        data = await self._request(
            method, path, json=json_body, params=params, extra_headers=extra_headers
        )
        if data is None:
            raise BackendAPIError(
                204,
                "No Content",
                {
                    "type": "https://api.backend.ai/probs/unexpected-no-content",
                    "title": f"Expected a JSON response from {method} {path}, but got 204 No Content",
                },
            )
        return cast(ResponseT, response_model.model_validate(data))


class BackendAIAppProxyClient:
    """HTTP client for direct-to-deployment endpoints fronted by Backend.AI's app-proxy.

    Unlike :class:`BackendAIAuthClient` (which signs requests with HMAC against
    the Backend.AI manager API), this client targets the runtime's own HTTP
    surface (vLLM / SGLang / NIM / TGI / custom) and uses an optional
    ``Authorization: Bearer <token>`` header. The deployment endpoint URL is
    supplied per-request, not via :attr:`ClientConfig.endpoint`.

    Owns the aiohttp session. Domain clients (e.g.
    :class:`ai.backend.client.v2.deployment_chat.DeploymentChatClient`) take an
    instance of this class via :class:`BaseAppProxyDomainClient` and add the
    contract-specific request methods (e.g. chat-completions, /generate, etc.).
    """

    _config: ClientConfig
    _session: aiohttp.ClientSession

    def __init__(self, config: ClientConfig) -> None:
        self._config = config
        self._session = _create_aiohttp_session(config)

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
                payload = await self._parse_response(resp)
                self._raise_for_status(resp, payload)
                return payload
        except aiohttp.ClientConnectionError as e:
            raise BackendClientError(f"failed to reach deployment endpoint: {e!r}") from e

    @staticmethod
    async def _parse_response(resp: aiohttp.ClientResponse) -> dict[str, Any]:
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
                f"deployment endpoint returned non-JSON response (status={resp.status}): {raw!r}"
            ) from e
        if not isinstance(payload, dict):
            raise BackendClientError(
                f"deployment endpoint returned non-object payload "
                f"(type={type(payload).__name__}, status={resp.status}): {payload!r}"
            )
        return payload

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
            raise DeploymentAuthError(resp.status, resp.reason or "Unauthorized", payload)
        raise BackendAPIError(resp.status, resp.reason or "HTTP error", payload)
