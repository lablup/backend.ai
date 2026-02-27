"""Backward-compatible shim for the service (model serving) module.

The actual handler logic has been migrated to
``ai.backend.manager.api.rest.service.handler.ServiceHandler``.
This module keeps ``create_app()`` working so that existing server bootstrap
(which still mounts legacy sub-applications) is not broken.

Once ``server.py`` is updated to register new-style routes, this file can be
removed entirely.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable
from typing import TYPE_CHECKING

import aiohttp_cors
import aiotools
import attrs
from aiohttp import web

from ai.backend.common.dto.manager.model_serving.request import ServiceFilterModel
from ai.backend.logging import BraceStyleAdapter

from .rest.middleware.auth import auth_required
from .rest.routing import _wrap_api_handler
from .rest.service.handler import ServiceHandler
from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))

# Re-export for backward compatibility (used by adapter.py)
__all__ = ("ServiceFilterModel",)


def _lazy_handler(
    method_name: str,
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]:
    """Create a handler that lazily instantiates ServiceHandler on first request.

    The ``ServiceHandler`` requires ``Processors`` at construction time, but
    ``Processors`` is not available when ``create_app()`` is called.  This
    factory defers creation to the first actual request, when
    ``request.app["_root.context"]`` is already populated.
    """
    _cache: dict[str, Callable[[web.Request], Awaitable[web.StreamResponse]]] = {}

    async def handler(request: web.Request) -> web.StreamResponse:
        if "wrapped" not in _cache:
            root_ctx: RootContext = request.app["_root.context"]
            instance = ServiceHandler(processors=root_ctx.processors)
            method = getattr(instance, method_name)
            _cache["wrapped"] = _wrap_api_handler(method)
        return await _cache["wrapped"](request)

    return handler


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    await app_ctx.database_ptask_group.shutdown()


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "services"
    app["api_versions"] = (4, 5)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["services.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route

    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", auth_required(_lazy_handler("list_serve"))))
    cors.add(root_resource.add_route("POST", auth_required(_lazy_handler("create"))))
    cors.add(add_route("POST", "/_/search", auth_required(_lazy_handler("search_services"))))
    cors.add(add_route("POST", "/_/try", auth_required(_lazy_handler("try_start"))))
    cors.add(
        add_route("GET", "/_/runtimes", auth_required(_lazy_handler("list_supported_runtimes")))
    )
    cors.add(add_route("GET", "/{service_id}", auth_required(_lazy_handler("get_info"))))
    cors.add(add_route("DELETE", "/{service_id}", auth_required(_lazy_handler("delete"))))
    cors.add(add_route("GET", "/{service_id}/errors", auth_required(_lazy_handler("list_errors"))))
    cors.add(
        add_route("POST", "/{service_id}/errors/clear", auth_required(_lazy_handler("clear_error")))
    )
    cors.add(add_route("POST", "/{service_id}/scale", auth_required(_lazy_handler("scale"))))
    cors.add(add_route("POST", "/{service_id}/sync", auth_required(_lazy_handler("sync"))))
    cors.add(
        add_route(
            "PUT",
            "/{service_id}/routings/{route_id}",
            auth_required(_lazy_handler("update_route")),
        )
    )
    cors.add(
        add_route(
            "DELETE",
            "/{service_id}/routings/{route_id}",
            auth_required(_lazy_handler("delete_route")),
        )
    )
    cors.add(
        add_route("POST", "/{service_id}/token", auth_required(_lazy_handler("generate_token")))
    )
    return app, []
