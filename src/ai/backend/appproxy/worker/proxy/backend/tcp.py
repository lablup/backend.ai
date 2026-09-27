import asyncio
import logging
import socket
from typing import Any, Final, override

from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.common.cron import LocalCron
from ai.backend.logging.structured import StructuredLogger

from .base import BaseBackend
from .last_access_marker import LastAccessMarkerTask
from .pool import RoutePool

log = StructuredLogger(logging.getLogger(__spec__.name))

MAX_BUFFER_SIZE: Final[int] = 1 * 1024 * 1024


class TCPBackend(BaseBackend):
    """TCP proxy backend that keeps routes in a health-checked pool.

    Route selection defers to the pool so that upstreams with repeated
    connect failures are excluded from traffic. The pool also tracks
    route identity by ``(host, port)`` and treats ``route_id`` changes on
    the same endpoint as kernel swaps (fresh health state).
    """

    _pool: RoutePool

    def __init__(self, routes: list[RouteInfo], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._pool = RoutePool(initial_routes=routes)

    @override
    async def update_routes(self, routes: list[RouteInfo]) -> None:
        await self._pool.update(routes)

    @override
    async def close(self) -> None:
        await self._pool.close()

    async def bind(
        self, down_reader: asyncio.StreamReader, down_writer: asyncio.StreamWriter
    ) -> None:
        metrics = self.root_context.metrics
        total_bytes = 0
        stop_event = asyncio.Event()

        async def _pipe(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            tag: str = "(unknown)",
        ) -> None:
            nonlocal total_bytes

            try:
                while True:
                    data = await reader.read(n=MAX_BUFFER_SIZE)
                    if not data:
                        break
                    total_bytes += len(data)
                    metrics.proxy.observe_upstream_tcp_traffic_chunk(len(data))
                    writer.write(data)
                    await writer.drain()
            except ConnectionResetError:
                log.trace("{}: connection reset", tag)
            finally:
                stop_event.set()

        route = await self._pool.select()
        log.trace(
            "proxying TCP connection to {}:{}",
            route.current_kernel_host,
            route.kernel_port,
            route_id=route.route_id,
        )

        marker_cron = LocalCron([LastAccessMarkerTask(self, route)])
        await marker_cron.start()
        await self.increase_request_counter()

        try:
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # unlike .frontend.tcp this has a chance of being a blocking call since kernel host can be a domain
            try:
                await asyncio.get_running_loop().run_in_executor(
                    None, sock.connect, (route.current_kernel_host, route.kernel_port)
                )
            except OSError as e:
                self._pool.record_failure(route)
                log.trace("app refused the connection: {!r}", e, route_id=route.route_id)
                sock.close()
                return

            up_reader, up_writer = await asyncio.open_connection(sock=sock)
            self._pool.record_success(route)
            async with asyncio.TaskGroup() as group:
                group.create_task(_pipe(up_reader, down_writer, tag="up->down"))
                group.create_task(_pipe(down_reader, up_writer, tag="down->up"))
        finally:
            metrics.proxy.observe_upstream_tcp_traffic_chunk(total_bytes)
            await marker_cron.stop()
            down_writer.close()
            await down_writer.wait_closed()
        log.trace("TCP connection closed")
