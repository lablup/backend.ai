"""Backward-compatibility shim for the etcd (config) module.

All handler logic has been migrated to:

* ``api.rest.etcd`` — EtcdHandler + register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(which mounts subapps via ``create_app``) continues to work.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Iterable
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.manager.api.rest.etcd import register_routes
from ai.backend.manager.api.rest.routing import RouteRegistry

from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext


async def app_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.pidx == 0:
        await root_ctx.config_provider.legacy_etcd_config_loader.register_myself()
    yield
    if root_ctx.pidx == 0:
        await root_ctx.config_provider.legacy_etcd_config_loader.deregister_myself()


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.cleanup_ctx.append(app_ctx)
    app["prefix"] = "config"
    app["api_versions"] = (3, 4)
    registry = RouteRegistry(app, default_cors_options)
    register_routes(registry)
    return app, []
