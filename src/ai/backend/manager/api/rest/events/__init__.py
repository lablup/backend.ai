"""New-style events module using RouteRegistry and constructor DI."""

from __future__ import annotations

from ai.backend.manager.api.manager import READ_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import EventsHandler


def register_routes(
    registry: RouteRegistry,
) -> None:
    """Register events routes on the given RouteRegistry."""
    handler = EventsHandler()
    _mw = [server_status_required(READ_ALLOWED), auth_required]

    registry.add("GET", r"/session", handler.push_session_events, middlewares=_mw)
    registry.add("GET", r"/background-task", handler.push_background_task_events, middlewares=_mw)
