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

    if (
        deps.db is None
        or deps.event_hub is None
        or deps.event_fetcher is None
        or deps.event_dispatcher is None
    ):
        raise RuntimeError(
            "Events module requires db, event_hub, event_fetcher, event_dispatcher in ModuleDeps"
        )

    # Capture narrowed (non-None) references for use in closures.
    db = deps.db
    event_hub = deps.event_hub
    event_fetcher = deps.event_fetcher
    event_dispatcher = deps.event_dispatcher

    reg = RouteRegistry.create("events", deps.cors_options)
    ctx = PrivateContext()

    # Wire lifecycle hooks — capture deps via closure
    reg.app.on_shutdown.append(lambda app: events_shutdown(app, ctx, event_hub=event_hub))
    reg.app.cleanup_ctx.append(
        lambda app: events_app_ctx(
            app,
            event_dispatcher=event_dispatcher,
            event_hub=event_hub,
        )
    )

    handler = EventsHandler(
        private_ctx=ctx,
        db=db,
        event_hub=event_hub,
        event_fetcher=event_fetcher,
        event_dispatcher=event_dispatcher,
    )
    _mw = [server_status_required(READ_ALLOWED, deps.config_provider), auth_required]

    reg.add("GET", r"/session", handler.push_session_events, middlewares=_mw)
    reg.add("GET", r"/background-task", handler.push_background_task_events, middlewares=_mw)
    return reg
