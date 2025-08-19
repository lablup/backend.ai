import asyncio
import functools
import logging
import socket
import time

from aiohttp import web

from ai.backend.appproxy.common.exceptions import (
    ServerMisconfiguredError,
)
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.proxy.backend import TCPBackend
from ai.backend.appproxy.worker.types import (
    Circuit,
    PortFrontendInfo,
    RootContext,
)
from ai.backend.logging import BraceStyleAdapter

from .base import BaseFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class TCPFrontend(BaseFrontend[TCPBackend, int]):
    servers: list[asyncio.Server]
    server_tasks: list[asyncio.Task]

    root_context: RootContext

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.servers = []
        self.server_tasks = []

    async def start(self) -> None:
        proxy_worker_config = self.root_context.local_config.proxy_worker
        port_proxy_config = proxy_worker_config.port_proxy
        if not port_proxy_config:
            raise ServerMisconfiguredError("worker:proxy-worker.port-proxy")
        port_start, port_end = port_proxy_config.bind_port_range
        for port in range(port_start, port_end + 1):
            service_host = port_proxy_config.bind_host
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
            port_proxy_config.bind_host,
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

    async def list_inactive_circuits(self, threshold: int) -> list[Circuit]:
        now = time.time()
        return [
            self.circuits[key]
            for key, backend in self.backends.items()
            if (backend.last_used - now) >= threshold
        ]

    async def pipe(
        self, circuit_key: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        metrics = self.root_context.metrics
        backend: TCPBackend | None = self.backends.get(circuit_key)

        if not backend:
            writer.close()
            await writer.wait_closed()
            return

        circuit_id = str(backend.circuit.id)

        start = time.monotonic()
        try:
            metrics.proxy.observe_downstream_tcp_start()
            await backend.bind(reader, writer)
        except Exception:
            log.exception("TCPFrontend.pipe(k: {}, c: {}):", circuit_key, circuit_id)
            raise
        finally:
            end = time.monotonic()
            metrics.proxy.observe_downstream_tcp_end(duration=int(end - start))

    def get_circuit_key(self, circuit: Circuit) -> int:
        assert isinstance(circuit.frontend, PortFrontendInfo)
        return circuit.frontend.port
