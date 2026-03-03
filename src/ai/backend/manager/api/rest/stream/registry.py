"""Stream module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

import aiotools

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import READ_ALLOWED, server_status_required

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_stream_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the stream sub-application."""
    from .handler import PrivateContext, StreamHandler, stream_app_ctx, stream_shutdown

    reg = RouteRegistry.create("stream", deps.cors_options)
    ctx = PrivateContext()

    # Store ctx on app dict for backward compatibility (lifecycle functions
    # fall back to app["stream.context"] when priv_ctx is None).
    reg.app["stream.context"] = ctx

    # PersistentTaskGroups required by stream handlers and shutdown logic
    reg.app["database_ptask_group"] = aiotools.PersistentTaskGroup()
    reg.app["rpc_ptask_group"] = aiotools.PersistentTaskGroup()

    # Wire lifecycle hooks — capture ctx via closure
    reg.app.cleanup_ctx.append(lambda app: stream_app_ctx(app, ctx))
    reg.app.on_shutdown.append(lambda app: stream_shutdown(app, ctx))

    handler = StreamHandler(private_ctx=ctx)
    _mw = [server_status_required(READ_ALLOWED, deps.config_provider), auth_required]

    reg.add("GET", r"/session/{session_name}/pty", handler.stream_pty, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/execute", handler.stream_execute, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/apps", handler.get_stream_apps, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/httpproxy", handler.stream_proxy, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/tcpproxy", handler.stream_proxy, middlewares=_mw)
    return reg
