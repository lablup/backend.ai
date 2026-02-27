"""Backward-compatibility shim for the container-registry module.

All handler logic has been migrated to:

* ``api.rest.container_registry`` — ContainerRegistryHandler + register_routes()

This module keeps ``create_app()`` so that the existing server bootstrap
(which mounts subapps via ``create_app``) continues to work.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web

from ai.backend.manager.api.rest.container_registry import register_routes
from ai.backend.manager.api.rest.routing import RouteRegistry

from .types import CORSOptions, WebMiddleware


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "container-registries"
    registry = RouteRegistry(app, default_cors_options)
    register_routes(registry)
    return app, []
