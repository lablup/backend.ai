from __future__ import annotations

from collections.abc import Sequence

import aiohttp_cors
from aiohttp import web

from .types import CORSOptions, RouteMiddleware, WebRequestHandler


class RouteRegistry:
    """Registry for API routes with per-route middleware support.

    Replaces the per-module create_app() + sub-app pattern by providing
    a unified way to register routes with optional route-level middleware
    on a single application.

    Global middleware (request_id, exception, auth, etc.) is applied via
    web.Application's middleware stack. Route-level middleware (auth_required,
    admin_required, rate limiting, etc.) is applied per-route through this
    registry's add() method.
    """

    def __init__(self, app: web.Application, cors_options: CORSOptions) -> None:
        self._app = app
        self._cors = aiohttp_cors.setup(app, defaults=cors_options)

    @property
    def app(self) -> web.Application:
        return self._app

    @property
    def cors(self) -> aiohttp_cors.CorsConfig:
        return self._cors

    def add(
        self,
        method: str,
        path: str,
        handler: WebRequestHandler,
        middlewares: Sequence[RouteMiddleware] | None = None,
    ) -> web.AbstractRoute:
        """Register a route with optional per-route middleware.

        Middlewares are applied in declaration order — the first middleware
        in the list becomes the outermost wrapper (executed first on request,
        last on response), matching the conventional decorator stacking order.

        Example::

            registry.add("GET", "/users", get_users, middlewares=[
                auth_required,        # checked first
                admin_required,       # checked second
            ])

        is equivalent to::

            @auth_required
            @admin_required
            async def get_users(request): ...
        """
        final_handler: WebRequestHandler = handler
        if middlewares:
            final_handler = _apply_route_middlewares(handler, middlewares)
        route = self._app.router.add_route(method, path, final_handler)
        self._cors.add(route)
        return route


def _apply_route_middlewares(
    handler: WebRequestHandler,
    middlewares: Sequence[RouteMiddleware],
) -> WebRequestHandler:
    """Wrap a handler with a chain of route-level middlewares.

    Middlewares are applied so that the first element in the list
    is the outermost wrapper, preserving standard decorator order.
    """
    wrapped: WebRequestHandler = handler
    for middleware in reversed(middlewares):
        wrapped = middleware(wrapped)
    return wrapped
