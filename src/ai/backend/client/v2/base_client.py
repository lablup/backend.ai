from __future__ import annotations

import ssl
from collections.abc import AsyncIterator, Iterable, Mapping
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, TypeVar

import aiohttp

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.api_handlers import (
    BaseRequestModel,
    BaseResponseModel,
)

from .auth import AuthStrategy
from .config import ClientConfig
from .exceptions import SSEError, WebSocketError, map_status_to_exception
from .streaming_types import SSEConnection, WebSocketSession

ResponseT = TypeVar("ResponseT", bound=BaseResponseModel)


class BackendAIClient:
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
    ) -> BackendAIClient:
        ssl_context: ssl.SSLContext | bool = not config.skip_ssl_verification
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(
            sock_connect=config.connection_timeout or None,
            sock_read=config.read_timeout or None,
        )
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        )
        return cls(config, auth, session)

    async def close(self) -> None:
        await self._session.close()

    def _build_url(self, path: str) -> str:
        base = str(self._config.endpoint).rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

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
    ) -> dict[str, Any] | None:
        session = self._session
        content_type = "application/json"
        rel_url = "/" + path.lstrip("/")
        headers = self._sign(method, rel_url, content_type)
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
            result: dict[str, Any] = await resp.json()
            return result

    async def typed_request(
        self,
        method: str,
        path: str,
        *,
        request: BaseRequestModel | None = None,
        response_model: type[ResponseT],
        params: dict[str, str] | None = None,
    ) -> ResponseT:
        json_body = request.model_dump(exclude_none=True) if request is not None else None
        data = await self._request(method, path, json=json_body, params=params)
        if data is None:
            raise BackendAPIError(
                204,
                "No Content",
                {
                    "type": "https://api.backend.ai/probs/unexpected-no-content",
                    "title": f"Expected a JSON response from {method} {path}, but got 204 No Content",
                },
            )
        return response_model.model_validate(data)

    async def typed_request_no_content(
        self,
        method: str,
        path: str,
        *,
        request: BaseRequestModel | None = None,
        params: dict[str, str] | None = None,
    ) -> None:
        json_body = request.model_dump(exclude_none=True) if request is not None else None
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
