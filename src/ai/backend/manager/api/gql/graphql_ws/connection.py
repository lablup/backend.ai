"""WebSocket connection wrapper for the graphql-transport-ws protocol.

Encapsulates ``aiohttp.web.WebSocketResponse`` and exposes typed
send/receive methods so that the handler never touches the raw WS object.

The connection is split into :class:`WSReceiver` (read) and
:class:`WSSender` (write/close), accessible via ``conn.receiver``
and ``conn.sender``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any, Final

from aiohttp import WSMsgType, web
from pydantic import TypeAdapter, ValidationError
from strawberry.types.execution import ExecutionResult, PreExecutionError

from ai.backend.logging import BraceStyleAdapter

from .types import (
    ClientMessage,
    ConnectionAckMessage,
    ErrorMessage,
    GQLWSMessageType,
    NextMessage,
    NextPayload,
    PongMessage,
    ServerCompleteMessage,
    ServerMessage,
)

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_PROTOCOL: Final = "graphql-transport-ws"
_client_message_adapter: Final[TypeAdapter[ClientMessage]] = TypeAdapter(ClientMessage)


class WSReceiver:
    """Read-side view of a graphql-transport-ws connection."""

    def __init__(self, ws: web.WebSocketResponse) -> None:
        self._ws = ws

    async def receive_init(self, *, wait_seconds: float) -> bool:
        """Wait for a ``connection_init`` message within the timeout.

        Returns ``True`` if a valid ``connection_init`` was received,
        ``False`` otherwise (timeout or wrong message type).
        """
        try:
            msg = await asyncio.wait_for(self._ws.receive(), timeout=wait_seconds)
        except TimeoutError:
            return False
        if msg.type != WSMsgType.TEXT:
            return False
        data: dict[str, Any] = msg.json()
        return data.get("type") == GQLWSMessageType.CONNECTION_INIT

    async def __aiter__(self) -> AsyncIterator[ClientMessage]:
        """Yield validated Pydantic client messages until the connection closes.

        Unknown or malformed messages are logged and skipped.
        """
        async for msg in self._ws:
            if msg.type == WSMsgType.TEXT:
                data: dict[str, Any] = msg.json()
                try:
                    yield _client_message_adapter.validate_python(data)
                except ValidationError:
                    log.warning("GQL WS: ignoring malformed client message: {}", data)
            elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                break


class WSSender:
    """Write-side view of a graphql-transport-ws connection."""

    def __init__(self, ws: web.WebSocketResponse) -> None:
        self._ws = ws

    @property
    def closed(self) -> bool:
        return self._ws.closed

    # ------------------------------------------------------------------
    # Send — Server → Client messages
    # ------------------------------------------------------------------

    async def send_ack(self) -> None:
        await self._send(ConnectionAckMessage())

    async def send_next(self, sub_id: str, result: ExecutionResult) -> None:
        payload = NextPayload(
            data=result.data,
            errors=[dict(e.formatted) for e in result.errors] if result.errors else None,
        )
        await self._send(NextMessage(id=sub_id, payload=payload))

    async def send_pre_execution_error(self, sub_id: str, error: PreExecutionError) -> None:
        errors = [dict(e.formatted) for e in error.errors] if error.errors else []
        await self._send(ErrorMessage(id=sub_id, payload=errors))

    async def send_internal_error(self, sub_id: str) -> None:
        await self._send(ErrorMessage(id=sub_id, payload=[{"message": "Internal server error"}]))

    async def send_complete(self, sub_id: str) -> None:
        await self._send(ServerCompleteMessage(id=sub_id))

    async def send_pong(self) -> None:
        await self._send(PongMessage())

    async def _send(self, msg: ServerMessage) -> None:
        await self._ws.send_json(msg.model_dump(exclude_none=True))

    # ------------------------------------------------------------------
    # Close — one method per protocol close reason
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Normal close."""
        if not self._ws.closed:
            await self._ws.close()

    async def close_init_timeout(self) -> None:
        """Close: client did not send ``connection_init`` in time (4408)."""
        if not self._ws.closed:
            await self._ws.close(code=4408, message=b"Connection initialisation timeout")

    async def close_unauthorized(self) -> None:
        """Close: first message was not ``connection_init`` (4401)."""
        if not self._ws.closed:
            await self._ws.close(code=4401, message=b"Unauthorized")

    async def close_duplicate_subscriber(self) -> None:
        """Close: client reused an existing subscription ID (4409)."""
        if not self._ws.closed:
            await self._ws.close(code=4409, message=b"Subscriber already exists")


class GraphQLWSConnection:
    """Lifecycle owner for a graphql-transport-ws WebSocket connection.

    Provides ``receiver`` and ``sender`` views for reading and writing.
    """

    def __init__(self, ws: web.WebSocketResponse) -> None:
        self._ws = ws
        self.receiver = WSReceiver(ws)
        self.sender = WSSender(ws)

    @classmethod
    async def open(
        cls,
        request: web.Request,
        *,
        max_msg_size: int,
    ) -> GraphQLWSConnection:
        ws = web.WebSocketResponse(
            protocols=[_PROTOCOL],
            max_msg_size=max_msg_size,
        )
        await ws.prepare(request)
        return cls(ws)

    async def wait_connection_init(self, *, wait_seconds: float) -> bool:
        """Wait for ``connection_init`` and send ``connection_ack``.

        Returns ``True`` on success, ``False`` if the client timed out
        or an error occurred (the connection is closed in that case).
        """
        try:
            received = await self.receiver.receive_init(wait_seconds=wait_seconds)
            if not received:
                await self.sender.close_init_timeout()
                return False
            await self.sender.send_ack()
            return True
        except Exception as e:
            log.exception("GQL WS: error during connection initialization (error: {})", repr(e))
            await self.sender.close()
            return False

    @property
    def handler_return(self) -> web.WebSocketResponse:
        """Access the underlying ``WebSocketResponse`` (for returning from aiohttp handlers)."""
        return self._ws
