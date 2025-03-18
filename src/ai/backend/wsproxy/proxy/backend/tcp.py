import asyncio
import logging
import random
import socket
from typing import Final

from ai.backend.logging import BraceStyleAdapter
from ai.backend.wsproxy.exceptions import WorkerNotAvailable
from ai.backend.wsproxy.types import RouteInfo

from .abc import AbstractBackend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

MAX_BUFFER_SIZE: Final[int] = 1 * 1024 * 1024


class TCPBackend(AbstractBackend):
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
        stop_event = asyncio.Event()

        async def _pipe(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            tag="(unknown)",
        ) -> None:
            try:
                while True:
                    data = await reader.read(n=MAX_BUFFER_SIZE)
                    if not data:
                        break
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

        route = self.selected_route
        log.debug(
            "Proxying TCP Request to {}:{}",
            route.kernel_host,
            route.kernel_port,
        )

        try:
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # unlike .frontend.tcp this has a chance of being a blocking call since kernel host can be a domain
            await asyncio.get_running_loop().run_in_executor(
                None, sock.connect, (route.kernel_host, route.kernel_port)
            )

            up_reader, up_writer = await asyncio.open_connection(sock=sock)
            log.debug(
                "Connected to {}:{}",
                route.kernel_host,
                route.kernel_port,
            )
            async with asyncio.TaskGroup() as group:
                group.create_task(_pipe(up_reader, down_writer, tag="up->down"))
                group.create_task(_pipe(down_reader, up_writer, tag="down->up"))
        finally:
            log.debug("tasks ended")
            down_writer.close()
            await down_writer.wait_closed()
        log.debug("TCP connection closed")
