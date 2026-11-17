import importlib.resources
import logging
import ssl
from typing import Any, override

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.worker.config import WildcardDomainConfig
from ai.backend.appproxy.worker.errors.ingress import IngressFrontendNotRegisteredError
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    IngressFrontend,
    IngressFrontendKind,
    IngressProtocol,
    WildcardFrontend,
)
from ai.backend.logging.structured import StructuredLogger, with_log_context

from .base import BaseHTTPFrontend

log = StructuredLogger(logging.getLogger(__spec__.name))


class SubdomainFrontend(BaseHTTPFrontend):
    site: web.TCPSite | None
    wildcard_config: WildcardDomainConfig

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.site = None
        if not self.root_context.local_config.proxy_worker.wildcard_domain:
            raise ServerMisconfiguredError("worker:proxy-worker.wildcard-domain")
        self.wildcard_config = self.root_context.local_config.proxy_worker.wildcard_domain

    @override
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
        # Resolve the real client IP from X-Forwarded-For first (only when trusted
        # proxies are configured) so request.remote is the real client before any
        # other middleware or the proxy handler reads it.
        if self._xff_strict is not None:
            app.middlewares.append(self._xff_strict.middleware)
        app.middlewares.extend([
            self.ensure_ingress_middleware,
            self.metric_collector_middleware,
            self.exception_middleware,
        ])
        app.router.add_route("*", "/{path:.*$}", self.proxy)

        with importlib.resources.as_file(
            importlib.resources.files("ai.backend.appproxy.common")
        ) as f:
            template_path = f / "templates"
            aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))

        runner = web.AppRunner(
            app,
            keepalive_timeout=30.0,
            max_field_size=self.root_context.local_config.proxy_worker.max_header_field_size,
            auto_decompress=False,  # transparently pass the request body
        )
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
        log.info("accepting proxy requests", service_addr=str(service_addr))

    @override
    async def stop(self) -> None:
        if self.site:
            await self.site.stop()

    def parse_subdomain(self, request: web.Request) -> str:
        # exclude port number when evaluating the subdomain
        subdomain = request.host.partition(":")[0].replace(self.wildcard_config.domain, "").lower()
        if not subdomain:
            raise IngressFrontendNotRegisteredError("E20009: No subdomain in the request host")
        return subdomain

    @web.middleware
    async def ensure_ingress_middleware(
        self, request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        async def _exception_safe_handler(request: web.Request) -> web.StreamResponse:
            subdomain = self.parse_subdomain(request)
            frontend_key = IngressFrontend(
                kind=IngressFrontendKind.WILDCARD,
                protocol=IngressProtocol.HTTP,
                wildcard=WildcardFrontend(subdomain=subdomain),
            ).key()
            ingress = await self._read_registered_ingress(frontend_key)
            backend = self.backends.get(frontend_key)
            if backend is None:
                raise IngressFrontendNotRegisteredError(
                    f"E20009: Subdomain {subdomain} not registered"
                )
            # TODO: Use the ingress id once ingresses are stored as their own entity.
            with with_log_context(circuit_id=backend.circuit_id):
                self.ensure_allowed_ip(request, ingress.access)
                self.ensure_credential(request, ingress, backend)
                request["backend"] = backend
                return await handler(request)

        return await self.exception_safe_handler_wrapper(request, _exception_safe_handler)
