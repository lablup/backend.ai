"""Backward-compatible create_app() shim for the artifact registry module.

All artifact registry handler logic has been migrated to:

* ``api.rest.artifact_registry.handler`` — ArtifactRegistryHandler class
* ``api.rest.artifact_registry`` — route registration

This module keeps the ``create_app()`` entry-point so that
``server.py`` continues to mount the sub-application without modification.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.manager.api.rest.artifact_registry.handler import ArtifactRegistryHandler
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "artifact-registries"

    handler = ArtifactRegistryHandler()
    registry = RouteRegistry(app, default_cors_options)
    _middlewares = [auth_required]

    registry.add("POST", "/scan", handler.scan_artifacts, middlewares=_middlewares)
    registry.add(
        "POST", "/delegation/scan", handler.delegate_scan_artifacts, middlewares=_middlewares
    )
    registry.add(
        "POST", "/delegation/import", handler.delegate_import_artifacts, middlewares=_middlewares
    )
    registry.add("POST", "/search", handler.search_artifacts, middlewares=_middlewares)
    registry.add("GET", "/model/{model_id}", handler.scan_single_model, middlewares=_middlewares)
    registry.add("POST", "/models/batch", handler.scan_models, middlewares=_middlewares)

    async def _bind_processors(app: web.Application) -> None:
        root_ctx: RootContext = app["_root.context"]
        handler.bind_processors(root_ctx.processors)

    app.on_startup.insert(0, _bind_processors)

    return app, []
