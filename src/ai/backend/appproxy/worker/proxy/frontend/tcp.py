import asyncio
import functools
import logging
import socket
import time
from typing import Any, override

from ai.backend.appproxy.common.config import ContentEncodingConfig
from ai.backend.appproxy.common.errors import (
    ServerMisconfiguredError,
    WorkerNotAvailable,
)
from ai.backend.appproxy.worker.errors.ingress import IngressFrontendNotRegisteredError
from ai.backend.appproxy.worker.proxy.backend import TCPBackend
from ai.backend.appproxy.worker.proxy.backend.tcp import TCPBackendArgs
from ai.backend.appproxy.worker.types import Circuit, RootContext
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressFrontend,
    IngressFrontendKind,
    IngressProtocol,
    PortFrontend,
)
from ai.backend.logging.structured import StructuredLogger, with_log_context

from .base import BaseFrontend

log = StructuredLogger(logging.getLogger(__spec__.name))


class TCPFrontend(BaseFrontend[TCPBackend]):
    servers: list[asyncio.Server]
    server_tasks: list[asyncio.Task[Any]]

    root_context: RootContext

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.servers = []
        self.server_tasks = []

    @override
    def apply_content_encoding_config(self, config: ContentEncodingConfig) -> None:
        # A raw TCP stream carries no Content-Encoding.
        pass

    @override
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
            "accepting proxy requests",
            bind_host=port_proxy_config.bind_host,
            port_range_start=port_start,
            port_range_end=port_end,
        )

    async def _listen_task(self, port: int, server: asyncio.Server) -> None:
        try:
            async with server:
                await server.serve_forever()
        except Exception:
            log.exception("TCP proxy listener failed", port=port)
            raise

    @override
    async def stop(self) -> None:
        for task in self.server_tasks:
            task.cancel()
            await task
        for server in self.servers:
            server.close()
            await server.wait_closed()

    def _is_peer_allowed(self, writer: asyncio.StreamWriter, access: IngressAccess) -> bool:
        # TCP carries no forwarded-for header, so the allowlist is matched
        # against the direct connection peer only.
        peername = writer.get_extra_info("peername")
        peer_ip = peername[0] if peername else None
        if not self._is_client_ip_allowed(peer_ip, access):
            log.trace("rejecting TCP client {} (not in allowed_client_ips)", peer_ip)
            return False
        return True

    @override
    async def initialize_backend(
        self, ingress: Ingress, circuit: Circuit | None = None
    ) -> TCPBackend:
        return TCPBackend(
            TCPBackendArgs(
                last_used_time_mark_queue=self.root_context.last_used_time_mark_queue,
                request_counter_key_queue=self.root_context.request_counter_key_queue,
                metrics=self.root_context.metrics,
                ingress=ingress,
                circuit=circuit,
            )
        )

    @override
    async def terminate_backend(self, backend: TCPBackend) -> None:
        await backend.close()

    async def _close_writer(self, writer: asyncio.StreamWriter) -> None:
        writer.close()
        await writer.wait_closed()

    async def pipe(
        self, port: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        metrics = self.root_context.metrics
        frontend_key = IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.TCP,
            port=PortFrontend(number=port),
        ).key()
        backend = self.backends.get(frontend_key)
        if backend is None:
            await self._close_writer(writer)
            return

        # TODO: Use the ingress id once ingresses are stored as their own entity.
        with with_log_context(circuit_id=backend.circuit_id):
            try:
                ingress = await self._read_registered_ingress(frontend_key)
            except IngressFrontendNotRegisteredError:
                log.trace("rejecting a TCP connection to a frontend with no ingress")
                await self._close_writer(writer)
                return
            if not self._is_peer_allowed(writer, ingress.access):
                await self._close_writer(writer)
                return

            start = time.monotonic()
            try:
                metrics.proxy.observe_downstream_tcp_start()
                await backend.bind(reader, writer)
            except WorkerNotAvailable:
                log.trace("no healthy route for the TCP connection")
            except Exception:
                log.exception("failed to proxy a TCP connection")
            finally:
                end = time.monotonic()
                metrics.proxy.observe_downstream_tcp_end(duration=int(end - start))
