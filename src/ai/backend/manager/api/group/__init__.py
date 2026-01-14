"""
Group (project) API module providing REST API handlers for group operations.
"""

from __future__ import annotations

from collections.abc import Iterable

import aiohttp_cors
from aiohttp import web

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.types import CORSOptions, WebMiddleware

from .handler import GroupAPIHandler

__all__ = ("create_app",)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for group API endpoints."""
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "group"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = GroupAPIHandler()

    # Wrap handlers with server_status_required decorator
    cors.add(
        app.router.add_route(
            "POST",
            "/registry-quota",
            server_status_required(READ_ALLOWED)(handler.create_registry_quota),
        )
    )
    cors.add(
        app.router.add_route(
            "GET",
            "/registry-quota",
            server_status_required(READ_ALLOWED)(handler.read_registry_quota),
        )
    )
    cors.add(
        app.router.add_route(
            "PATCH",
            "/registry-quota",
            server_status_required(READ_ALLOWED)(handler.update_registry_quota),
        )
    )
    cors.add(
        app.router.add_route(
            "DELETE",
            "/registry-quota",
            server_status_required(READ_ALLOWED)(handler.delete_registry_quota),
        )
    )

    return app, []
