from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.client.v2.streaming_types import SSEConnection, WebSocketSession
from ai.backend.common.dto.manager.streaming import (
    GetStreamAppsResponse,
    StreamProxyParams,
)

_STREAM_BASE = "/stream/session"
_EVENTS_BASE = "/events"


class StreamingClient(BaseDomainClient):
    """Client for WebSocket, SSE, and REST streaming endpoints.

    WebSocket operations return async context managers yielding
    :class:`WebSocketSession` instances.  SSE operations return async
    context managers yielding :class:`SSEConnection` instances that
    can be iterated asynchronously.
    """

    # -----------------------------------------------------------------------
    # WebSocket — Terminal PTY
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def connect_terminal(
        self,
        session_name: str,
    ) -> AsyncIterator[WebSocketSession]:
        """Open a PTY WebSocket session for *session_name*."""
        async with self._client.ws_connect(
            f"{_STREAM_BASE}/{session_name}/pty",
        ) as ws:
            yield ws

    # -----------------------------------------------------------------------
    # WebSocket — Code execution
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def connect_execute(
        self,
        session_name: str,
    ) -> AsyncIterator[WebSocketSession]:
        """Open a code-execution WebSocket session for *session_name*."""
        async with self._client.ws_connect(
            f"{_STREAM_BASE}/{session_name}/execute",
        ) as ws:
            yield ws

    # -----------------------------------------------------------------------
    # WebSocket — HTTP proxy
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def connect_http_proxy(
        self,
        session_name: str,
        params: StreamProxyParams,
    ) -> AsyncIterator[WebSocketSession]:
        """Open an HTTP-proxy WebSocket to a service inside *session_name*."""
        async with self._client.ws_connect(
            f"{_STREAM_BASE}/{session_name}/httpproxy",
            params={k: str(v) for k, v in params.model_dump(exclude_none=True).items()},
        ) as ws:
            yield ws

    # -----------------------------------------------------------------------
    # WebSocket — TCP proxy
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def connect_tcp_proxy(
        self,
        session_name: str,
        params: StreamProxyParams,
    ) -> AsyncIterator[WebSocketSession]:
        """Open a TCP-proxy WebSocket to a service inside *session_name*."""
        async with self._client.ws_connect(
            f"{_STREAM_BASE}/{session_name}/tcpproxy",
            params={k: str(v) for k, v in params.model_dump(exclude_none=True).items()},
        ) as ws:
            yield ws

    # -----------------------------------------------------------------------
    # SSE — Session events
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def subscribe_session_events(
        self,
        *,
        session_name: str = "*",
        owner_access_key: str | None = None,
        session_id: UUID | None = None,
        group_name: str = "*",
        scope: str = "*",
    ) -> AsyncIterator[SSEConnection]:
        """Subscribe to session lifecycle events via SSE."""
        params: dict[str, str] = {
            "name": session_name,
            "group": group_name,
            "scope": scope,
        }
        if owner_access_key is not None:
            params["ownerAccessKey"] = owner_access_key
        if session_id is not None:
            params["sessionId"] = str(session_id)
        async with self._client.sse_connect(
            f"{_EVENTS_BASE}/session",
            params=params,
        ) as sse:
            yield sse

    # -----------------------------------------------------------------------
    # SSE — Background task events
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def subscribe_background_task_events(
        self,
        task_id: UUID,
    ) -> AsyncIterator[SSEConnection]:
        """Subscribe to background-task progress events via SSE."""
        async with self._client.sse_connect(
            f"{_EVENTS_BASE}/background-task",
            params={"taskId": str(task_id)},
        ) as sse:
            yield sse

    # -----------------------------------------------------------------------
    # REST — Stream apps
    # -----------------------------------------------------------------------

    async def get_stream_apps(
        self,
        session_name: str,
    ) -> GetStreamAppsResponse:
        """List available streaming apps/services for *session_name*."""
        data = await self._client._request(
            "GET",
            f"{_STREAM_BASE}/{session_name}/apps",
        )
        return GetStreamAppsResponse.model_validate(data)
