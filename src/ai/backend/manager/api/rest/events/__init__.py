from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_events_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry

__all__ = ["register_events_module"]


def register_routes(registry: RouteRegistry) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_events_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.

    NOTE: When called from server.py, the PrivateContext is expected to be
    already stored on ``registry.app["events.context"]`` before this
    function is invoked.
    """
    from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import EventsHandler, PrivateContext

    # Reuse the context that server.py pre-installs, or create a fresh one.
    ctx = registry.app.get("events.context") or PrivateContext()
    handler = EventsHandler(private_ctx=ctx)
    _mw = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("GET", r"/session", handler.push_session_events, middlewares=_mw)
    registry.add("GET", r"/background-task", handler.push_background_task_events, middlewares=_mw)
