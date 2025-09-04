import importlib.resources
import logging
import ssl

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.appproxy.common.exceptions import GenericBadRequest, ServerMisconfiguredError
from ai.backend.logging import BraceStyleAdapter

from ....types import Circuit, PortFrontendInfo
from .base import BaseHTTPFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class PortFrontend(BaseHTTPFrontend[int]):
    sites: list[web.TCPSite]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.sites = []

    async def start(self) -> None:
        ssl_ctx = None
        proxy_worker_config = self.root_context.local_config.proxy_worker
        if proxy_worker_config.tls_listen:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                str(proxy_worker_config.tls_cert),
                str(proxy_worker_config.tls_privkey),
            )
        port_proxy_config = proxy_worker_config.port_proxy
        if not port_proxy_config:
            raise ServerMisconfiguredError("worker:proxy-worker.port-proxy")
        port_start, port_end = port_proxy_config.bind_port_range
        for port in range(port_start, port_end + 1):
            app = web.Application()
            app["port"] = port
            app.on_response_prepare.append(self.append_cors_headers)
            # ensure_slot middleware should be placed before exception_middleware and metric_collector_middleware
            # so that metric_collector_middleware can properly assess circuit variable
            # Keep in mind that implementation of ensure_slot_middleware should manually handle exception and respond with
            # appropriate HTTP response, which usually is automatically covered by exception_middleware
            # That can be achieved by wraping whole execution block with AbstractHTTPFrontend.exception_safe_handler_wrapper()
            app.middlewares.extend([
                self.ensure_slot_middleware,
                self.metric_collector_middleware,
                self.exception_middleware,
            ])
            app.router.add_route("*", "/{path:.*$}", self.proxy)

            with importlib.resources.as_file(
                importlib.resources.files("ai.backend.appproxy.common")
            ) as f:
                template_path = f / "templates"
                aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))

            runner = web.AppRunner(app, keepalive_timeout=30.0)
            await runner.setup()
            service_host = port_proxy_config.bind_host
            site = web.TCPSite(
                runner,
                service_host,
                port,
                backlog=1024,
                reuse_port=True,
                ssl_context=ssl_ctx,
            )
            await site.start()
            self.sites.append(site)
        log.info(
            "accepting proxy requests from {}:{}~{}",
            port_proxy_config.bind_host,
            port_start,
            port_end,
        )

    async def stop(self) -> None:
        for site in self.sites:
            await site.stop()

    @web.middleware
    async def ensure_slot_middleware(
        self, request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        port: int = request.app["port"]
        circuit = self.circuits.get(port, None)
        if circuit is None:
            raise GenericBadRequest(f"Unregistered slot {port}")
        self.ensure_credential(request, circuit)
        backend = self.backends[port]
        request["circuit"] = circuit
        request["backend"] = backend
        return await handler(request)

    def get_circuit_key(self, circuit: Circuit) -> int:
        assert isinstance(circuit.frontend, PortFrontendInfo)
        return circuit.frontend.port
