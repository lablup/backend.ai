"""Events module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import EventsHandler

if TYPE_CHECKING:
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.manager.api.rest.types import RouteDeps


def register_events_routes(
    handler: EventsHandler,
    route_deps: RouteDeps,
    *,
    event_hub: EventHub,
) -> RouteRegistry:
    """Build the events sub-application."""
    from .handler import PrivateContext, events_shutdown

    reg = RouteRegistry.create("events", route_deps.cors_options)
    ctx = PrivateContext()

    # Wire lifecycle hooks — capture deps via closure
    reg.app.on_shutdown.append(lambda app: events_shutdown(app, ctx, event_hub=event_hub))

    _mw = [route_deps.read_status_mw, auth_required]

    reg.add("GET", r"/session", handler.push_session_events, middlewares=_mw)
    reg.add("GET", r"/background-task", handler.push_background_task_events, middlewares=_mw)
    return reg
