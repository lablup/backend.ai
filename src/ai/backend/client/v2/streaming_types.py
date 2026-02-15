from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import aiohttp

from .exceptions import WebSocketError

log = logging.getLogger(__spec__.name)


@dataclass(frozen=True, slots=True)
class SSEEvent:
    """A single Server-Sent Event."""

    event: str
    data: str
    id: str | None = None
    retry: int | None = None


class WebSocketSession:
    """Thin async wrapper around :class:`aiohttp.ClientWebSocketResponse`.

    Provides send/receive helpers and async iteration over incoming messages.
    Operations on a closed session raise :class:`WebSocketError`.
    """

    __slots__ = ("_ws",)

    def __init__(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        self._ws = ws

    @property
    def closed(self) -> bool:
        return self._ws.closed

    def _check_open(self) -> None:
        if self._ws.closed:
            raise WebSocketError("WebSocket connection is closed")

    async def send_str(self, data: str) -> None:
        self._check_open()
        await self._ws.send_str(data)

    async def send_bytes(self, data: bytes) -> None:
        self._check_open()
        await self._ws.send_bytes(data)

    async def send_json(self, data: Any) -> None:
        self._check_open()
        await self._ws.send_json(data)

    async def receive_str(self) -> str:
        self._check_open()
        return await self._ws.receive_str()

    async def receive_bytes(self) -> bytes:
        self._check_open()
        return await self._ws.receive_bytes()

    async def receive_json(self) -> Any:
        self._check_open()
        return await self._ws.receive_json()

    async def close(self) -> None:
        if not self._ws.closed:
            await self._ws.close()

    def __aiter__(self) -> AsyncIterator[aiohttp.WSMessage]:
        return self._ws.__aiter__()


class SSEConnection:
    """Wraps an :class:`aiohttp.ClientResponse` and parses the SSE stream.

    Use as an async iterator to consume :class:`SSEEvent` instances::

        async with client.sse_connect("/events") as events:
            async for event in events:
                print(event.event, event.data)
    """

    __slots__ = ("_response",)

    def __init__(self, response: aiohttp.ClientResponse) -> None:
        self._response = response

    async def close(self) -> None:
        self._response.close()

    def __aiter__(self) -> AsyncIterator[SSEEvent]:
        return self._iter_events()

    async def _iter_events(self) -> AsyncIterator[SSEEvent]:
        msg_lines: list[str] = []
        while True:
            raw_line = await self._response.content.readline()
            if not raw_line:
                # Connection closed — yield any buffered event first.
                if msg_lines:
                    event = self._parse_event(msg_lines)
                    if event is not None:
                        yield event
                break

            line = raw_line.strip(b"\r\n")

            # Comment lines start with ":"
            if line.startswith(b":"):
                continue

            # Blank line = event boundary
            if not line:
                if not msg_lines:
                    continue
                event = self._parse_event(msg_lines)
                msg_lines.clear()
                if event is None:
                    continue
                yield event
                if event.event == "server_close":
                    break
                continue

            msg_lines.append(line.decode("utf-8"))

    @staticmethod
    def _parse_event(lines: list[str]) -> SSEEvent | None:
        event_type = "message"
        event_id: str | None = None
        event_retry: int | None = None
        data_lines: list[str] = []
        try:
            for stored_line in lines:
                hdr, text = stored_line.split(":", maxsplit=1)
                text = text.lstrip(" ")
                if hdr == "data":
                    data_lines.append(text)
                elif hdr == "event":
                    event_type = text
                elif hdr == "id":
                    event_id = text
                elif hdr == "retry":
                    event_retry = int(text)
        except (IndexError, ValueError):
            log.exception("SSEConnection: parsing error")
            return None
        return SSEEvent(
            event=event_type,
            data="\n".join(data_lines),
            id=event_id,
            retry=event_retry,
        )
