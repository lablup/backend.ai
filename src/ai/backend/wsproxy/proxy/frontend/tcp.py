import asyncio
import functools
import logging
import socket

from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.wsproxy.defs import RootContext
from ai.backend.wsproxy.proxy.backend import TCPBackend
from ai.backend.wsproxy.types import (
    Circuit,
    RouteInfo,
)

from .abc import AbstractFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class TCPFrontend(AbstractFrontend[TCPBackend, int]):
    servers: list[asyncio.Server]
    server_tasks: list[asyncio.Task]

    root_context: RootContext

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.servers = []
        self.server_tasks = []

    async def start(self) -> None:
        config = self.root_context.local_config.wsproxy
        port_start, port_end = config.bind_proxy_port_range
        for port in range(port_start, port_end + 1):
            service_host = config.bind_host
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # sock.bind() can be a blocking call only if
            # we're trying to bind to a UNIX domain file or host is not an IP address
            # so we don't have to wrap bind() call by run_in_executor()
            sock.bind((service_host, port))
            server = await asyncio.start_server(
                functools.partial(self.pipe, port),
                sock=sock,
            )
            self.servers.append(server)
            self.server_tasks.append(asyncio.create_task(self._listen_task(port, server)))
        log.info(
            "accepting proxy requests from {}:{}~{}",
            config.bind_host,
            port_start,
            port_end,
        )

    async def _listen_task(self, circuit_key: int, server: asyncio.Server) -> None:
        try:
            async with server:
                await server.serve_forever()
        except Exception:
            log.exception("TCPFrontend._listen_task(c: {}): exception:", circuit_key)
            raise

    async def stop(self) -> None:
        for task in self.server_tasks:
            task.cancel()
            await task
        for server in self.servers:
            server.close()
            await server.wait_closed()

    def ensure_credential(self, request: web.Request, circuit: Circuit) -> None:
        # TCP does not support authentication
        return

    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> TCPBackend:
        return TCPBackend(routes, self.root_context, circuit)

    async def update_backend(self, backend: TCPBackend, routes: list[RouteInfo]) -> TCPBackend:
        backend.routes = routes
        return backend

    async def terminate_backend(self, backend: TCPBackend) -> None:
        return

    async def pipe(
        self, circuit_key: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        backend: TCPBackend | None = self.backends.get(circuit_key)
        if not backend:
            writer.close()
            await writer.wait_closed()
            return

        try:
            await backend.bind(reader, writer)
        except Exception:
            log.exception("TCPFrontend.pipe(k: {}):", circuit_key)
            raise

    def get_circuit_key(self, circuit: Circuit) -> int:
        return circuit.port
