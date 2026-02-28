"""Fair Share REST API package (legacy shim).

The actual handler logic has been migrated to ``api.rest.fair_share``.
This module is kept only so that the old ``server.py`` sub-application
loader does not break until wiring is updated in BA-4753.
"""

from __future__ import annotations

from collections.abc import Iterable

from aiohttp import web

from ai.backend.manager.api.types import CORSOptions, WebMiddleware


def create_app(
    _default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "fair-share"
    return app, []


__all__ = ("create_app",)
