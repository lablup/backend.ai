"""Backward-compatibility shim for the group config module.

All group config (dotfile) logic has been migrated to:

* ``api.rest.groupconfig`` — GroupConfigHandler + route registration

This module keeps ``create_app()`` so that the existing server bootstrap
(``server.py``) continues to work without modification.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import TYPE_CHECKING

import aiohttp_cors
from aiohttp import web

from ai.backend.manager.api.rest.groupconfig.handler import GroupConfigHandler
from ai.backend.manager.api.rest.middleware.auth import admin_required, auth_required
from ai.backend.manager.api.rest.routing import _wrap_api_handler

from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext

_status_readable = server_status_required(READ_ALLOWED)


def _lazy_handler(
    method_name: str,
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]:
    """Create a handler that lazily instantiates GroupConfigHandler on first request.

    The ``GroupConfigHandler`` requires ``Processors`` at construction time, but
    ``Processors`` is not available when ``create_app()`` is called.  This
    factory defers creation to the first actual request, when
    ``request.app["_root.context"]`` is already populated.
    """
    _cache: dict[str, Callable[[web.Request], Awaitable[web.StreamResponse]]] = {}

    async def handler(request: web.Request) -> web.StreamResponse:
        if "wrapped" not in _cache:
            root_ctx: RootContext = request.app["_root.context"]
            instance = GroupConfigHandler(
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
    app["prefix"] = "group-config"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route

    cors.add(
        add_route(
            "POST",
            "/dotfiles",
            _status_readable(admin_required(_lazy_handler("create"))),
        )
    )
    cors.add(
        add_route(
            "GET",
            "/dotfiles",
            _status_readable(auth_required(_lazy_handler("list_or_get"))),
        )
    )
    cors.add(
        add_route(
            "PATCH",
            "/dotfiles",
            _status_readable(admin_required(_lazy_handler("update"))),
        )
    )
    cors.add(
        add_route(
            "DELETE",
            "/dotfiles",
            _status_readable(admin_required(_lazy_handler("delete"))),
        )
    )
    return app, []
