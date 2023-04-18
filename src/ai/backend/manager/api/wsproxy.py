"""
WebSocket-based streaming kernel interaction APIs.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Awaitable, Callable, Optional, Union

import aiohttp
import aiotools
from aiohttp import WSCloseCode, web

from ai.backend.common.logging import BraceStyleAdapter

from ..config import DEFAULT_CHUNK_SIZE

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class ServiceProxy(metaclass=ABCMeta):
    """
    The abstract base class to implement service proxy handlers.
    """

    __slots__ = (
        "ws",
        "host",
        "port",
        "downstream_cb",
        "upstream_cb",
        "ping_cb",
    )

    def __init__(
        self,
        down_ws: web.WebSocketResponse,
        dest_host: str,
        dest_port: int,
        *,
        downstream_callback: Callable[[Any], Awaitable[None]] = None,
        upstream_callback: Callable[[Any], Awaitable[None]] = None,
        ping_callback: Callable[[Any], Awaitable[None]] = None,
    ) -> None:
        self.ws = down_ws
        self.host = dest_host
        self.port = dest_port
        self.downstream_cb = downstream_callback
        self.upstream_cb = upstream_callback
        self.ping_cb = ping_callback

    @abstractmethod
    async def proxy(self) -> web.WebSocketResponse:
        pass


class TCPProxy(ServiceProxy):
    __slots__ = (
        *ServiceProxy.__slots__,
        "down_task",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.down_task: Optional[asyncio.Task] = None

    async def proxy(self) -> web.WebSocketResponse:
        try:
            try:
                log.debug("Trying to open proxied TCP connection to {}:{}", self.host, self.port)
                reader, writer = await asyncio.open_connection(self.host, self.port)
            except ConnectionRefusedError:
                await self.ws.close(code=WSCloseCode.TRY_AGAIN_LATER)
                return self.ws
            except Exception:
                log.exception("TCPProxy.proxy(): unexpected initial connection error")
                await self.ws.close(code=WSCloseCode.INTERNAL_ERROR)
                return self.ws

            async def downstream() -> None:
                try:
                    while True:
                        try:
                            chunk = await reader.read(DEFAULT_CHUNK_SIZE)
                            if not chunk:
                                break
                            await self.ws.send_bytes(chunk)
                        except (RuntimeError, ConnectionResetError, asyncio.CancelledError):
                            # connection interrupted by client-side
                            break
                        else:
                            if self.downstream_cb is not None:
                                await self.downstream_cb(chunk)
                except asyncio.CancelledError:
                    pass
                except Exception:
                    log.exception("TCPProxy.proxy(): unexpected downstream error")
                finally:
                    await self.ws.close(code=WSCloseCode.GOING_AWAY)

            log.debug("TCPProxy connected {0}:{1}", self.host, self.port)
            self.down_task = asyncio.create_task(downstream())
            async for msg in self.ws:
                if msg.type == web.WSMsgType.BINARY:
                    try:
                        writer.write(msg.data)
                        await writer.drain()
                    except RuntimeError:
                        log.debug("Error on writing: Is it closed?")
                    if self.upstream_cb is not None:
                        await self.upstream_cb(msg.data)
                elif msg.type == web.WSMsgType.PING:
                    await self.ws.pong(msg.data)
                    if self.ping_cb is not None:
                        await self.ping_cb(msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    log.debug("TCPProxy.proxy(): websocket upstream error", exc_info=msg.data)
                    writer.close()
                    await writer.wait_closed()

        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("TCPProxy.proxy(): unexpected upstream error")
        finally:
            if self.down_task is not None and not self.down_task.done():
                self.down_task.cancel()
                await self.down_task
            log.debug("websocket connection closed")
        return self.ws


class WebSocketProxy:
    __slots__ = (
        "up_conn",
        "down_conn",
        "upstream_buffer",
        "upstream_buffer_task",
        "downstream_cb",
        "upstream_cb",
        "ping_cb",
    )

    up_conn: aiohttp.ClientWebSocketResponse
    down_conn: web.WebSocketResponse
    # FIXME: use __future__.annotations in Python 3.7+
    upstream_buffer: asyncio.Queue  # contains: Tuple[Union[bytes, str], web.WSMsgType]
    upstream_buffer_task: Optional[asyncio.Task]
    downstream_cb: Callable[[str | bytes], Awaitable[None]] | None
    upstream_cb: Callable[[str | bytes], Awaitable[None]] | None
    ping_cb: Callable[[str | bytes], Awaitable[None]] | None

    def __init__(
        self,
        up_conn: aiohttp.ClientWebSocketResponse,
        down_conn: web.WebSocketResponse,
        *,
        downstream_callback: Callable[[str | bytes], Awaitable[None]] = None,
        upstream_callback: Callable[[str | bytes], Awaitable[None]] = None,
        ping_callback: Callable[[str | bytes], Awaitable[None]] = None,
    ):
        self.up_conn = up_conn
        self.down_conn = down_conn
        self.upstream_buffer = asyncio.Queue()
        self.upstream_buffer_task = None
        self.downstream_cb = downstream_callback
        self.upstream_cb = upstream_callback
        self.ping_cb = ping_callback

    async def proxy(self) -> None:
        asyncio.create_task(self.downstream())
        await self.upstream()

    async def upstream(self) -> None:
        try:
            async for msg in self.down_conn:
                if msg.type in (web.WSMsgType.TEXT, web.WSMsgType.binary):
                    await self.write(msg.data, msg.type)
                    if self.upstream_cb is not None:
                        await self.upstream_cb(msg.data)
                elif msg.type == web.WSMsgType.PING:
                    if self.ping_cb is not None:
                        await self.ping_cb(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    log.error("ws connection closed with exception {}", self.up_conn.exception())
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    break
            # here, client gracefully disconnected
        except asyncio.CancelledError:
            # here, client forcibly disconnected
            raise
        finally:
            await self.close_downstream()

    async def downstream(self) -> None:
        try:
            async with aiotools.PersistentTaskGroup() as tg:
                self.upstream_buffer_task = tg.create_task(
                    self.consume_upstream_buffer(),
                )
                async for msg in self.up_conn:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self.down_conn.send_str(msg.data)
                        if self.downstream_cb is not None:
                            await asyncio.shield(tg.create_task(self.downstream_cb(msg.data)))
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        await self.down_conn.send_bytes(msg.data)
                        if self.downstream_cb is not None:
                            await asyncio.shield(tg.create_task(self.downstream_cb(msg.data)))
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
            # here, server gracefully disconnected
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("unexpected error")
        finally:
            await self.close_upstream()

    async def consume_upstream_buffer(self) -> None:
        while True:
            msg, tp = await self.upstream_buffer.get()
            try:
                if self.up_conn and not self.up_conn.closed:
                    if tp == aiohttp.WSMsgType.TEXT:
                        await self.up_conn.send_str(msg)
                    elif tp == aiohttp.WSMsgType.binary:
                        await self.up_conn.send_bytes(msg)
                else:
                    await self.close_downstream()
            finally:
                self.upstream_buffer.task_done()

    async def write(self, msg: Union[bytes, str], tp: web.WSMsgType) -> None:
        await self.upstream_buffer.put((msg, tp))

    async def close_downstream(self) -> None:
        if not self.down_conn.closed:
            await self.down_conn.close()

    async def close_upstream(self) -> None:
        if self.upstream_buffer_task:
            self.upstream_buffer_task.cancel()
            await self.upstream_buffer_task
        if self.up_conn:
            await self.up_conn.close()
