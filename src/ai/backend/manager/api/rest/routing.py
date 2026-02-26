from __future__ import annotations

from collections.abc import Sequence

import aiohttp_cors
from aiohttp import web

from .types import CORSOptions, RouteMiddleware, WebMiddleware, WebRequestHandler


class RouteRegistry:
    """Registry for API routes with three-tier middleware support.

    Middleware tiers (outermost → innermost):

    1. **Global middleware** — added to ``web.Application.middlewares``,
       processed by aiohttp for every request (e.g. request_id, exception,
       auth, rate-limit).
    2. **Registry-level middleware** — applied to every route registered
       through this registry instance (e.g. auth_required for an entire
       module).
    3. **Route-level middleware** — applied to individual routes via the
       ``add()`` method (e.g. admin_required on a specific endpoint).

    When both registry-level and route-level middlewares are present,
    they are concatenated (registry first, then route) and applied as a
    single chain in declaration order.
    """

    def __init__(
        self,
        app: web.Application,
        cors_options: CORSOptions,
        *,
        global_middlewares: Sequence[WebMiddleware] | None = None,
        middlewares: Sequence[RouteMiddleware] | None = None,
    ) -> None:
        self._app = app
        self._cors = aiohttp_cors.setup(app, defaults=cors_options)
        self._middlewares: list[RouteMiddleware] = list(middlewares or [])
        if global_middlewares:
            app.middlewares.extend(global_middlewares)

    @property
    def app(self) -> web.Application:
        return self._app

    @property
    def cors(self) -> aiohttp_cors.CorsConfig:
        return self._cors

    @property
    def middlewares(self) -> list[RouteMiddleware]:
        return self._middlewares

    def add(
        self,
        method: str,
        path: str,
        handler: WebRequestHandler,
        middlewares: Sequence[RouteMiddleware] | None = None,
    ) -> web.AbstractRoute:
        """Register a route with optional per-route middleware.

        Registry-level middlewares are prepended to the per-route list,
        so they wrap the handler outermost. Within each tier, the first
        middleware in the list becomes the outermost wrapper (executed
        first on request, last on response), matching the conventional
        decorator stacking order.

        Example::

            registry = RouteRegistry(app, cors, middlewares=[auth_required])
            registry.add("GET", "/admin/users", list_users, middlewares=[
                admin_required,
            ])

        is equivalent to::

            @auth_required      # registry-level (outermost)
            @admin_required     # route-level
            async def list_users(request): ...
        """
        combined = self._middlewares + list(middlewares or [])
        final_handler: WebRequestHandler = handler
        if combined:
            final_handler = _apply_route_middlewares(handler, combined)
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
