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

    if (
        deps.db is None
        or deps.registry is None
        or deps.error_monitor is None
        or deps.valkey_live is None
        or deps.idle_checker_host is None
        or deps.etcd is None
        or deps.event_dispatcher is None
    ):
        raise RuntimeError(
            "Stream module requires db, registry, error_monitor, valkey_live,"
            " idle_checker_host, etcd, event_dispatcher in ModuleDeps"
        )

    # Capture narrowed (non-None) references for use in closures.
    db = deps.db
    registry = deps.registry
    error_monitor = deps.error_monitor
    valkey_live = deps.valkey_live
    idle_checker_host = deps.idle_checker_host
    etcd = deps.etcd
    event_dispatcher = deps.event_dispatcher

    reg = RouteRegistry.create("stream", deps.cors_options)
    ctx = PrivateContext()

    # PersistentTaskGroups required by stream handlers and shutdown logic
    reg.app["database_ptask_group"] = aiotools.PersistentTaskGroup()
    reg.app["rpc_ptask_group"] = aiotools.PersistentTaskGroup()

    # Wire lifecycle hooks — capture deps via closure
    reg.app.cleanup_ctx.append(
        lambda app: stream_app_ctx(
            app,
            ctx,
            db=db,
            valkey_live=valkey_live,
            etcd=etcd,
            idle_checker_host=idle_checker_host,
            event_dispatcher=event_dispatcher,
        )
    )
    reg.app.on_shutdown.append(lambda app: stream_shutdown(app, ctx))

    handler = StreamHandler(
        private_ctx=ctx,
        db=db,
        registry=registry,
        config_provider=deps.config_provider,
        error_monitor=error_monitor,
        valkey_live=valkey_live,
        idle_checker_host=idle_checker_host,
        etcd=etcd,
        event_dispatcher=event_dispatcher,
    )
    _mw = [server_status_required(READ_ALLOWED, deps.config_provider), auth_required]

    reg.add("GET", r"/session/{session_name}/pty", handler.stream_pty, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/execute", handler.stream_execute, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/apps", handler.get_stream_apps, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/httpproxy", handler.stream_proxy, middlewares=_mw)
    reg.add("GET", r"/session/{session_name}/tcpproxy", handler.stream_proxy, middlewares=_mw)
    return reg
