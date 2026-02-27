"""New-style stream module using RouteRegistry and constructor DI."""

from __future__ import annotations

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import StreamHandler


def register_routes(
    registry: RouteRegistry,
) -> None:
    """Register stream routes on the given RouteRegistry."""
    handler = StreamHandler()
    _mw = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("GET", r"/session/{session_name}/pty", handler.stream_pty, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/execute", handler.stream_execute, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/apps", handler.get_stream_apps, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/httpproxy", handler.stream_proxy, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/tcpproxy", handler.stream_proxy, middlewares=_mw)
