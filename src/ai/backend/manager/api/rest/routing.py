from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Final

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import APIStreamResponse, extract_param_value, parse_response
from ai.backend.logging import BraceStyleAdapter

from .types import ApiHandler, CORSOptions, RouteMiddleware, WebRequestHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.ratelimit.registry import (
        RatelimitContext as RatelimitPrivateContext,
    )

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
    """Registry for API routes with parent-child tree support.

    Each registry owns a ``web.Application`` and a URL prefix.  Registries
    form a tree via ``add_subregistry()``.  At mount time the tree is
    flattened by ``collect_apps()`` so that every sub-application is
    mounted directly on the root application (no nested subapps).

    Middleware tiers (outermost → innermost):

    1. **Registry-level middleware** — applied to every route registered
       through this registry instance (includes middlewares inherited from
       parent registries via ``add_subregistry()``).
    2. **Route-level middleware** — applied to individual routes via the
       ``add()`` method (e.g. admin_required on a specific endpoint).

    When both registry-level and route-level middlewares are present,
    they are concatenated (registry first, then route) and applied as a
    single chain in declaration order.
    """

    _prefix: str
    _app: web.Application
    _cors: aiohttp_cors.CorsConfig
    _middlewares: list[RouteMiddleware]
    _subregistries: dict[str, RouteRegistry]
    ratelimit_ctx: RatelimitPrivateContext | None

    def __init__(
        self,
        app: web.Application,
        cors_options: CORSOptions,
        *,
        prefix: str = "",
        middlewares: Sequence[RouteMiddleware] | None = None,
    ) -> None:
        self._prefix = prefix
        self._app = app
        self._cors = aiohttp_cors.setup(app, defaults=cors_options)
        self._middlewares = list(middlewares or [])
        self._subregistries = {}
        self.ratelimit_ctx = None

    @classmethod
    def create(
        cls,
        prefix: str,
        cors_options: CORSOptions,
        *,
        middlewares: Sequence[RouteMiddleware] = (),
    ) -> RouteRegistry:
        """Create a new sub-application with its own ``RouteRegistry``.

        The sub-application is not yet mounted; call ``add_subregistry()``
        on a parent registry to wire it into the tree, then use
        ``collect_apps()`` at mount time.
        """
        subapp = web.Application()
        subapp.on_response_prepare.append(_on_prepare)
        return cls(subapp, cors_options, prefix=prefix, middlewares=middlewares)

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def app(self) -> web.Application:
        return self._app

    @property
    def cors(self) -> aiohttp_cors.CorsConfig:
        return self._cors

    @property
    def middlewares(self) -> list[RouteMiddleware]:
        return self._middlewares

    def add_subregistry(self, child: RouteRegistry) -> None:
        """Register a child registry in the tree.

        Aggregates ``self.prefix + child.prefix`` into the child's stored
        prefix so that ``collect_apps()`` returns fully-qualified prefixes.
        Propagates parent middlewares into the child.
        Raises ``ValueError`` on duplicate prefix.
        """
        child_prefix = child.prefix
        if child_prefix in self._subregistries:
            raise ValueError(f"Sub-registry with prefix '{child_prefix}' already registered")
        # Propagate parent middlewares into child (parent outermost)
        child._middlewares = self._middlewares + child._middlewares
        # Aggregate prefix: "admin" + "domains" → "admin/domains"
        if self._prefix:
            child._prefix = f"{self._prefix}/{child._prefix}"
        self._subregistries[child_prefix] = child

    def find_subregistry(self, prefix: str) -> RouteRegistry | None:
        """Look up a direct sub-registry by its original (non-aggregated) prefix."""
        return self._subregistries.get(prefix)

    def collect_apps(self) -> list[tuple[str, web.Application, RouteRegistry]]:
        """Flatten the tree into ``(aggregated_prefix, app, registry)`` tuples.

        Example: admin registry (prefix="admin") with domain sub-registry
        (prefix="domains") yields::

            [("admin", admin_app, admin_reg),
             ("admin/domains", domain_app, domain_reg)]

        Leaf registries without routes are included only if they have no
        sub-registries (i.e. they are true leaves).
        """
        result: list[tuple[str, web.Application, RouteRegistry]] = []
        if list(self._app.router.routes()) or not self._subregistries:
            result.append((self._prefix, self._app, self))
        for child in self._subregistries.values():
            result.extend(child.collect_apps())
        return result

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

        Registry-level middlewares (including those inherited from parent
        registries) are prepended to the per-route list, so they wrap the
        handler outermost.

        Example::

            registry = RouteRegistry.create("admin", cors, middlewares=[auth_required])
            registry.add("GET", "/users", list_users, middlewares=[
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
