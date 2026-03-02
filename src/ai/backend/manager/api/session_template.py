"""Backward-compatible create_app() shim for the session template module.

All session template handler logic has been migrated to:

* ``api.rest.session_template.handler`` — SessionTemplateHandler class
* ``api.rest.session_template`` — route registration

This module keeps the ``create_app()`` entry-point so that
``server.py`` continues to mount the sub-application without modification.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import _wrap_api_handler
from ai.backend.manager.api.rest.session_template.handler import SessionTemplateHandler

from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext

_status_readable = server_status_required(READ_ALLOWED)


def _lazy_handler(
    method_name: str,
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]:
    """Create a handler that lazily instantiates SessionTemplateHandler on first request.

    The ``SessionTemplateHandler`` requires ``Processors`` at construction time, but
    ``Processors`` is not available when ``create_app()`` is called.  This
    factory defers creation to the first actual request, when
    ``request.app["_root.context"]`` is already populated.
    """
    _cache: dict[str, Callable[[web.Request], Awaitable[web.StreamResponse]]] = {}

    async def handler(request: web.Request) -> web.StreamResponse:
        if "wrapped" not in _cache:
            root_ctx: RootContext = request.app["_root.context"]
            instance = SessionTemplateHandler(
                processors=root_ctx.processors,
            )
            method = getattr(instance, method_name)
            _cache["wrapped"] = _wrap_api_handler(method)
        return await _cache["wrapped"](request)

    return handler


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "template/session"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route

    cors.add(
        add_route(
            "POST",
            "",
            _status_readable(auth_required(_lazy_handler("create"))),
        )
    )
    cors.add(
        add_route(
            "GET",
            "",
            _status_readable(auth_required(_lazy_handler("list_templates"))),
        )
    )
    cors.add(
        add_route(
            "GET",
            "/{template_id}",
            _status_readable(auth_required(_lazy_handler("get"))),
        )
    )
    cors.add(
        add_route(
            "PUT",
            "/{template_id}",
            _status_readable(auth_required(_lazy_handler("update"))),
        )
    )
    cors.add(
        add_route(
            "DELETE",
            "/{template_id}",
            _status_readable(auth_required(_lazy_handler("delete"))),
        )
    )
    return app, []
