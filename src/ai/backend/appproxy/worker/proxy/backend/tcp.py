import asyncio
import logging
import random
import socket
from typing import Final

import aiotools

from ai.backend.appproxy.common.exceptions import WorkerNotAvailable
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.logging import BraceStyleAdapter

from .base import BaseBackend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

MAX_BUFFER_SIZE: Final[int] = 1 * 1024 * 1024


class TCPBackend(BaseBackend):
    routes: list[RouteInfo]

    def __init__(self, routes: list[RouteInfo], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.routes = routes

    @property
    def selected_route(self) -> RouteInfo:
        if len(self.routes) == 0:
            raise WorkerNotAvailable
        elif len(self.routes) == 1:
            selected_route = self.routes[0]
            if selected_route.traffic_ratio == 0:
                raise WorkerNotAvailable
        else:
            ratios: list[float] = [r.traffic_ratio for r in self.routes]
            selected_route = random.choices(self.routes, weights=ratios, k=1)[0]
        return selected_route

    async def bind(
        self, down_reader: asyncio.StreamReader, down_writer: asyncio.StreamWriter
    ) -> None:
        metrics = self.root_context.metrics
        total_bytes = 0
        stop_event = asyncio.Event()

        async def _pipe(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            tag="(unknown)",
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
                    log.debug("TCPBackend._pipe(t: {}): sent {} bytes", tag, len(data))
            except ConnectionResetError:
                log.debug("Conn reset")
                pass
            except Exception:
                log.exception("")
                raise
            finally:
                log.debug("setting stop event")
                stop_event.set()

        async def _last_access_marker_task(interval: float) -> None:
            await self.mark_last_used_time(route)

        route = self.selected_route
        log.debug(
            "Proxying TCP Request to {}:{}",
            route.current_kernel_host,
            route.kernel_port,
        )

        marker_task = aiotools.create_timer(_last_access_marker_task, 1.5)
        await self.increase_request_counter()

        try:
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # unlike .frontend.tcp this has a chance of being a blocking call since kernel host can be a domain
            await asyncio.get_running_loop().run_in_executor(
                None, sock.connect, (route.current_kernel_host, route.kernel_port)
            )

            up_reader, up_writer = await asyncio.open_connection(sock=sock)
            log.debug(
                "Connected to {}:{}",
                route.current_kernel_host,
                route.kernel_port,
            )
            async with asyncio.TaskGroup() as group:
                group.create_task(_pipe(up_reader, down_writer, tag="up->down"))
                group.create_task(_pipe(down_reader, up_writer, tag="down->up"))
        finally:
            log.debug("tasks ended")
            metrics.proxy.observe_upstream_tcp_traffic_chunk(total_bytes)
            marker_task.cancel()
            await marker_task
            down_writer.close()
            await down_writer.wait_closed()
        log.debug("TCP connection closed")
