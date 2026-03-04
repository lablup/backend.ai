"""Stream module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import READ_ALLOWED, server_status_required

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps
    from ai.backend.manager.event_dispatcher.handlers.stream_cleanup import (
        StreamCleanupEventHandler,
    )


def register_stream_routes(
    deps: ModuleDeps,
    *,
    stream_cleanup_handler: StreamCleanupEventHandler,
) -> RouteRegistry:
    """Build the stream sub-application."""
    from .handler import PrivateContext, StreamHandler, stream_app_ctx, stream_shutdown

    stream_processors = deps.processors.stream
    error_monitor = deps.error_monitor

    reg = RouteRegistry.create("stream", deps.cors_options)
    ctx = PrivateContext()

    # Wire lifecycle hooks — capture deps via closure
    reg.app.cleanup_ctx.append(
        lambda app: stream_app_ctx(
            app,
            ctx,
            stream_processors=stream_processors,
            stream_cleanup_handler=stream_cleanup_handler,
        )
    )
    reg.app.on_shutdown.append(lambda app: stream_shutdown(app, ctx))

    handler = StreamHandler(
        private_ctx=ctx,
        stream_processors=stream_processors,
        config_provider=deps.config_provider,
        error_monitor=error_monitor,
    )
    _mw = [server_status_required(READ_ALLOWED, deps.config_provider), auth_required]

    reg.add("GET", r"/session/{session_name}/pty", handler.stream_pty, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/execute", handler.stream_execute, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/apps", handler.get_stream_apps, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/httpproxy", handler.stream_proxy, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/tcpproxy", handler.stream_proxy, middlewares=_mw)
    return reg
