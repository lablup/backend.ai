import importlib.resources
import logging

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.wsproxy.exceptions import GenericBadRequest
from ai.backend.wsproxy.types import Circuit

from .abc import AbstractHTTPFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class PortFrontend(AbstractHTTPFrontend[int]):
    sites: list[web.TCPSite]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.sites = []

    async def start(self) -> None:
        config = self.root_context.local_config.wsproxy
        port_start, port_end = config.bind_proxy_port_range
        for port in range(port_start, port_end + 1):
            app = web.Application()
            app["port"] = port
            app.middlewares.extend([
                self.cors_middleware,
                self.exception_middleware,
                self._ensure_slot,
            ])
            app.router.add_route("*", "/{path:.*$}", self.proxy)

            with importlib.resources.as_file(importlib.resources.files("ai.backend.wsproxy")) as f:
                template_path = f / "templates"
                aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))

            runner = web.AppRunner(app, keepalive_timeout=30.0)
            await runner.setup()
            service_host = config.bind_host
            site = web.TCPSite(
                runner,
                service_host,
                port,
                backlog=1024,
                reuse_port=True,
            )
            await site.start()
            self.sites.append(site)
        log.info(
            "accepting proxy requests from {}:{}~{}",
            config.bind_host,
            port_start,
            port_end,
        )

    async def stop(self) -> None:
        for site in self.sites:
            await site.stop()

    @web.middleware
    async def _ensure_slot(self, request: web.Request, handler: Handler) -> web.StreamResponse:
        port: int = request.app["port"]
        circuit = self.circuits[port]
        if not circuit:
            raise GenericBadRequest(f"Unregistered slot {port}")  # noqa: F821

        self.ensure_credential(request, circuit)
        circuit = self.circuits[port]
        backend = self.backends[port]
        request["circuit"] = circuit
        request["backend"] = backend
        return await handler(request)

    def get_circuit_key(self, circuit: Circuit) -> int:
        return circuit.port
