"""Events module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import READ_ALLOWED, server_status_required

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_events_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the events sub-application."""
    from .handler import EventsHandler, PrivateContext, events_app_ctx, events_shutdown

    reg = RouteRegistry.create("events", deps.cors_options)
    ctx = PrivateContext()

    # Store ctx on app dict for backward compatibility (lifecycle functions
    # fall back to app["events.context"] when priv_ctx is None).
    reg.app["events.context"] = ctx

    # Wire lifecycle hooks — capture ctx via closure
    reg.app.on_shutdown.append(lambda app: events_shutdown(app, ctx))
    reg.app.cleanup_ctx.append(events_app_ctx)

    handler = EventsHandler(private_ctx=ctx)
    _mw = [server_status_required(READ_ALLOWED, deps.config_provider), auth_required]

    reg.add("GET", r"/session", handler.push_session_events, middlewares=_mw)
    reg.add("GET", r"/background-task", handler.push_background_task_events, middlewares=_mw)
    return reg
