from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Sequence
from typing import Any, Final

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIStreamResponse, extract_param_value, parse_response
from ai.backend.logging import BraceStyleAdapter

from .types import ApiHandler, CORSOptions, RouteMiddleware, WebMiddleware, WebRequestHandler

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _handle_stream_response(
    request: web.Request,
    result: APIStreamResponse,
) -> web.StreamResponse:
    """Convert an ``APIStreamResponse`` into a ``web.StreamResponse`` with chunked streaming."""
    resp = web.StreamResponse(status=result.status, headers=result.headers)
    body_iter = result.body.read()

    try:
        first_chunk = await body_iter.__anext__()
        await resp.prepare(request)
        await resp.write(first_chunk)
    except Exception:
        log.exception("Failed to send first chunk from stream")
        raise web.HTTPInternalServerError(
            reason="Failed to initialize streaming response"
        ) from None

    try:
        async for chunk in body_iter:
            await resp.write(chunk)
        await resp.write_eof()
    except Exception:
        log.exception("Error during streaming response body iteration")
        resp.force_close()

    return resp


def _wrap_api_handler(handler: ApiHandler) -> WebRequestHandler:
    """Wrap a typed API handler: extract params from web.Request, convert APIResponse → web.Response."""
    sig = inspect.signature(handler, eval_str=True)

    @functools.wraps(handler)
    async def wrapped(request: web.Request) -> web.StreamResponse:
        kwargs: dict[str, Any] = {}
        for name, param in sig.parameters.items():
            kwargs[name] = await extract_param_value(request, param.annotation)
        response = await handler(**kwargs)
        if isinstance(response, web.StreamResponse):
            return response
        if isinstance(response, APIStreamResponse):
            return await _handle_stream_response(request, response)
        return parse_response(response)

    return wrapped


async def _on_prepare(_request: web.Request, response: web.StreamResponse) -> None:
    response.headers["Server"] = "BackendAI"


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

    _root_app: web.Application | None

    def __init__(
        self,
        app: web.Application,
        cors_options: CORSOptions,
        *,
        global_middlewares: Sequence[WebMiddleware] | None = None,
        middlewares: Sequence[RouteMiddleware] | None = None,
    ) -> None:
        self._app = app
        self._root_app = None
        self._cors = aiohttp_cors.setup(app, defaults=cors_options)
        self._middlewares: list[RouteMiddleware] = list(middlewares or [])
        if global_middlewares:
            app.middlewares.extend(global_middlewares)

    @classmethod
    def create_subapp(
        cls,
        root_app: web.Application,
        prefix: str,
        cors_options: CORSOptions,
        *,
        middlewares: Sequence[RouteMiddleware] = (),
        global_middlewares: Sequence[WebMiddleware] = (),
    ) -> RouteRegistry:
        """Create a new sub-application with its own ``RouteRegistry``.

        The sub-application is mounted at ``/{prefix}`` on *root_app* and
        automatically receives a bridge to the root context at startup.
        """
        subapp = web.Application()
        subapp["prefix"] = prefix

        async def _bridge_root_ctx(subapp: web.Application) -> None:
            subapp["_root.context"] = root_app["_root.context"]
            subapp["_root_app"] = root_app

        subapp.on_startup.insert(0, _bridge_root_ctx)
        subapp.on_response_prepare.append(_on_prepare)
        registry = cls(
            subapp,
            cors_options,
            middlewares=middlewares,
            global_middlewares=global_middlewares,
        )
        # Defer mounting: add_subapp() freezes the subapp (router +
        # signal lists), so routes must be registered first.  The
        # caller should invoke ``registry.mount()`` after registering
        # all routes.
        registry._root_app = root_app
        return registry

    def mount(self) -> None:
        """Mount the subapp on its root application.

        Must be called after all routes have been registered via
        ``add()`` because ``add_subapp()`` freezes the sub-application.
        Only meaningful for registries created via ``create_subapp()``.
        """
        if self._root_app is not None:
            self._root_app.add_subapp("/" + self._app["prefix"], self._app)
            self._root_app = None

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
        handler: ApiHandler,
        middlewares: Sequence[RouteMiddleware] | None = None,
    ) -> web.AbstractRoute:
        """Register a route with optional per-route middleware.

        The handler is always wrapped by ``_wrap_api_handler`` so that
        typed parameters (``BodyParam``, ``QueryParam``, ``MiddlewareParam``,
        etc.) are automatically extracted from the ``web.Request`` and the
        returned ``APIResponse`` is converted to a ``web.Response``.

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
        effective_handler: WebRequestHandler = _wrap_api_handler(handler)
        combined = self._middlewares + list(middlewares or [])
        final_handler: WebRequestHandler = effective_handler
        if combined:
            final_handler = _apply_route_middlewares(effective_handler, combined)
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
