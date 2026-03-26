"""Stream module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import StreamHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps
    from ai.backend.manager.event_dispatcher.handlers.stream_cleanup import (
        StreamCleanupEventHandler,
    )
    from ai.backend.manager.services.stream.processors import StreamProcessors


def register_stream_routes(
    handler: StreamHandler,
    route_deps: RouteDeps,
    *,
    stream_processors: StreamProcessors,
    stream_cleanup_handler: StreamCleanupEventHandler,
) -> RouteRegistry:
    """Build the stream sub-application."""
    from .handler import PrivateContext, stream_app_ctx, stream_shutdown

    reg = RouteRegistry.create("stream", route_deps.cors_options)
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

    _mw = [route_deps.read_status_mw, auth_required]

    reg.add("GET", r"/session/{session_name}/pty", handler.stream_pty, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/execute", handler.stream_execute, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/apps", handler.get_stream_apps, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/httpproxy", handler.stream_proxy, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/tcpproxy", handler.stream_proxy, middlewares=_mw)
    return reg
