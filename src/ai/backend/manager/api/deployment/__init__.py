"""Backward-compatibility shim for the deployment module.

All deployment handler logic has been migrated to:
* ``api.rest.deployment.handler`` — DeploymentAPIHandler (constructor DI)
* ``api.rest.deployment`` — register_routes()

This module keeps ``create_app()`` working for the legacy sub-app
bootstrap in ``server.py``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import aiohttp_cors
from aiohttp import web

from ai.backend.manager.api.rest.deployment.handler import DeploymentAPIHandler
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import _wrap_api_handler
from ai.backend.manager.api.types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

__all__ = ("create_app",)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for deployment API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "deployments"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = DeploymentAPIHandler()

    def _route(method: Any) -> Any:
        return auth_required(_wrap_api_handler(method))

    # Deployment routes
    cors.add(app.router.add_route("POST", "/", _route(handler.create_deployment)))
    cors.add(app.router.add_route("POST", "/search", _route(handler.search_deployments)))
    cors.add(app.router.add_route("GET", "/{deployment_id}", _route(handler.get_deployment)))
    cors.add(app.router.add_route("PATCH", "/{deployment_id}", _route(handler.update_deployment)))
    cors.add(app.router.add_route("DELETE", "/{deployment_id}", _route(handler.destroy_deployment)))

    # Revision routes (nested under deployment)
    cors.add(
        app.router.add_route(
            "POST", "/{deployment_id}/revisions/search", _route(handler.search_revisions)
        )
    )
    cors.add(
        app.router.add_route(
            "GET", "/{deployment_id}/revisions/{revision_id}", _route(handler.get_revision)
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{deployment_id}/revisions/{revision_id}/activate",
            _route(handler.activate_revision),
        )
    )
    cors.add(
        app.router.add_route(
            "POST",
            "/{deployment_id}/revisions/{revision_id}/deactivate",
            _route(handler.deactivate_revision),
        )
    )

    # Route routes (nested under deployment)
    cors.add(
        app.router.add_route(
            "POST", "/{deployment_id}/routes/search", _route(handler.search_routes)
        )
    )
    cors.add(
        app.router.add_route(
            "PATCH",
            "/{deployment_id}/routes/{route_id}/traffic-status",
            _route(handler.update_route_traffic_status),
        )
    )

    async def _bind_processors(app: web.Application) -> None:
        root_ctx: RootContext = app["_root.context"]
        handler.bind_processors(root_ctx.processors)

    app.on_startup.insert(0, _bind_processors)

    return app, []
