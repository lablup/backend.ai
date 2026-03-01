from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_stream_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry

__all__ = ["register_stream_module"]


def register_routes(registry: RouteRegistry) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_stream_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.

    NOTE: When called from server.py, the PrivateContext is expected to be
    already stored on ``registry.app["stream.context"]`` before this
    function is invoked.
    """
    from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import PrivateContext, StreamHandler

    # Reuse the context that server.py pre-installs, or create a fresh one.
    ctx = registry.app.get("stream.context") or PrivateContext()
    handler = StreamHandler(private_ctx=ctx)
    _mw = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("GET", r"/session/{session_name}/pty", handler.stream_pty, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/execute", handler.stream_execute, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/apps", handler.get_stream_apps, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/httpproxy", handler.stream_proxy, middlewares=_mw)
    registry.add("GET", r"/session/{session_name}/tcpproxy", handler.stream_proxy, middlewares=_mw)
