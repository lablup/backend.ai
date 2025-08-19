import importlib.resources
import logging
import ssl

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.appproxy.common.exceptions import GenericBadRequest, ServerMisconfiguredError
from ai.backend.logging import BraceStyleAdapter

from ....config import WildcardDomainConfig
from ....types import Circuit, SubdomainFrontendInfo
from .base import BaseHTTPFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class SubdomainFrontend(BaseHTTPFrontend[str]):
    site: web.TCPSite | None
    wildcard_config: WildcardDomainConfig

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.site = None
        if not self.root_context.local_config.proxy_worker.wildcard_domain:
            raise ServerMisconfiguredError("worker:proxy-worker.wildcard-domain")
        self.wildcard_config = self.root_context.local_config.proxy_worker.wildcard_domain

    async def start(self) -> None:
        ssl_ctx = None
        proxy_worker_config = self.root_context.local_config.proxy_worker
        if proxy_worker_config.tls_listen:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                str(proxy_worker_config.tls_cert),
                str(proxy_worker_config.tls_privkey),
            )
        app = web.Application()
        app.on_response_prepare.append(self.append_cors_headers)
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
        service_addr = self.wildcard_config.bind_addr
        site = web.TCPSite(
            runner,
            str(service_addr.host),
            service_addr.port,
            backlog=1024,
            reuse_port=True,
            ssl_context=ssl_ctx,
        )
        await site.start()
        self.site = site
        log.info("accepting proxy requests at {}", service_addr)

    async def stop(self) -> None:
        if self.site:
            await self.site.stop()

    def parse_slot(self, request: web.Request) -> str:
        # exclude port number when evaluating the subdomain
        subdomain = request.host.partition(":")[0].replace(self.wildcard_config.domain, "").lower()
        if subdomain not in self.circuits:
            raise GenericBadRequest(f"E20009: Subdomain {subdomain} not registered")
        return subdomain

    @web.middleware
    async def ensure_slot_middleware(
        self, request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        async def _exception_safe_handler(request: web.Request) -> web.StreamResponse:
            slot = self.parse_slot(request)
            circuit = self.circuits[slot]
            self.ensure_credential(request, circuit)
            backend = self.backends[slot]
            request["circuit"] = circuit
            request["backend"] = backend
            return await handler(request)

        return await self.exception_safe_handler_wrapper(request, _exception_safe_handler)

    def get_circuit_key(self, circuit: Circuit) -> str:
        assert isinstance(circuit.frontend, SubdomainFrontendInfo)
        return circuit.frontend.subdomain.lower()
