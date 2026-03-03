"""Backward-compatibility shim for the resource module.

Handler logic has been migrated to ``api.rest.resource.handler.ResourceHandler``.
``get_watcher_info()`` is preserved as a utility used by the vfolder module.
``get_container_registries`` is preserved as it is used by the etcd handler.

The ``create_app()`` shim has been removed because
``global_subapp_pkgs`` is no longer used by the server bootstrap.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import yarl
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter

from .auth import superadmin_required
from .types import WebRequestHandler

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# ------------------------------------------------------------------
# Utility kept for vfolder module
# ------------------------------------------------------------------


async def get_watcher_info(request: web.Request, agent_id: str) -> dict[str, Any]:
    """
    Get watcher information.

    :return addr: address of agent watcher (eg: http://127.0.0.1:6009)
    :return token: agent watcher token ("insecure" if not set in config server)
    """
    root_ctx: RootContext = request.app["_root.context"]
    token = root_ctx.config_provider.config.watcher.token
    if token is None:
        token = "insecure"
    agent_ip = await root_ctx.etcd.get(f"nodes/agents/{agent_id}/ip")
    raw_watcher_port = await root_ctx.etcd.get(
        f"nodes/agents/{agent_id}/watcher_port",
    )
    watcher_port = 6099 if raw_watcher_port is None else int(raw_watcher_port)
    addr = yarl.URL(f"http://{agent_ip}:{watcher_port}")
    return {
        "addr": addr,
        "token": token,
    }


# ------------------------------------------------------------------
# Lazy handler initialization helpers (kept for get_container_registries)
# ------------------------------------------------------------------

_HANDLER_APP_KEY = "_resource_handler_wrapped"


def _ensure_handler(app: web.Application) -> dict[str, WebRequestHandler]:
    """Lazily create ResourceHandler and wrap its methods on first request."""
    if _HANDLER_APP_KEY not in app:
        from ai.backend.manager.api.rest.resource.handler import ResourceHandler
        from ai.backend.manager.api.rest.routing import _wrap_api_handler

        root_ctx: RootContext = app["_root.context"]
        handler = ResourceHandler(processors=root_ctx.processors)
        app[_HANDLER_APP_KEY] = {
            name: _wrap_api_handler(getattr(handler, name))
            for name in ("get_container_registries",)
        }
    result: dict[str, WebRequestHandler] = app[_HANDLER_APP_KEY]
    return result


def _delegate(method_name: str) -> WebRequestHandler:
    """Return a handler function that delegates to the new-style ResourceHandler."""

    async def _handler(request: web.Request) -> web.StreamResponse:
        wrapped = _ensure_handler(request.app)
        return await wrapped[method_name](request)

    _handler.__name__ = method_name
    _handler.__qualname__ = f"resource._delegate.<{method_name}>"
    return _handler


# ------------------------------------------------------------------
# Backward-compatible re-export (used by rest/etcd/handler.py)
# ------------------------------------------------------------------

get_container_registries = superadmin_required(_delegate("get_container_registries"))
