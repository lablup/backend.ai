"""New-style session module using RouteRegistry and constructor DI."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from aiohttp import web

from ai.backend.common.api_handlers import extract_param_value, parse_response
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import SessionHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.api.rest.types import WebRequestHandler
    from ai.backend.manager.services.processors import Processors

# Re-export server_status_required from the legacy manager module so
# that the shim layer does not need its own import.
from ai.backend.manager.api.manager import (
    ALL_ALLOWED,
    READ_ALLOWED,
    server_status_required,
)


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register session routes on the given RouteRegistry.

    This is the forward-looking API for when ``server.py`` migrates to
    the ``register_routes()`` pattern.
    """
    handler = SessionHandler(processors=processors)

    # --- Session creation ---
    registry.add(
        "POST",
        "/session",
        handler.create_from_params,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/session/_/create",
        handler.create_from_params,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/session/_/create-from-template",
        handler.create_from_template,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/session/_/create-cluster",
        handler.create_cluster,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )

    # --- Session matching / utilities ---
    registry.add(
        "GET",
        "/session/_/match",
        handler.match_sessions,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/session/_/sync-agent-registry",
        handler.sync_agent_registry,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/session/_/transit-status",
        handler.check_and_transit_status,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED)],
    )

    # --- Task logs ---
    registry.add(
        "HEAD",
        "/session/_/logs",
        handler.get_task_logs,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        "/session/_/logs",
        handler.get_task_logs,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )

    # --- Per-session CRUD ---
    registry.add(
        "GET",
        r"/session/{session_name}",
        handler.get_info,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "PATCH",
        r"/session/{session_name}",
        handler.restart,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "DELETE",
        r"/session/{session_name}",
        handler.destroy,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}",
        handler.execute,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )

    # --- Per-session sub-resources ---
    registry.add(
        "GET",
        r"/session/{session_name}/direct-access-info",
        handler.get_direct_access_info,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/session/{session_name}/logs",
        handler.get_container_logs,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/rename",
        handler.rename_session,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/interrupt",
        handler.interrupt,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/complete",
        handler.complete,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/shutdown-service",
        handler.shutdown_service,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/upload",
        handler.upload_files,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/download",
        handler.download_files,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/download_single",
        handler.download_single,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
    registry.add(
        "GET",
        r"/session/{session_name}/files",
        handler.list_files,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/start-service",
        handler.start_service,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/commit",
        handler.commit_session,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/session/{session_name}/imagify",
        handler.convert_session_to_image,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED)],
    )
    registry.add(
        "GET",
        r"/session/{session_name}/commit",
        handler.get_commit_status,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/session/{session_name}/status-history",
        handler.get_status_history,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/session/{session_name}/abusing-report",
        handler.get_abusing_report,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/session/{session_name}/dependency-graph",
        handler.get_dependency_graph,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )


# ---------------------------------------------------------------------------
# Legacy sub-app support
# ---------------------------------------------------------------------------


def _make_lazy_handler(method_name: str) -> WebRequestHandler:
    """Create a standard aiohttp handler that lazily instantiates SessionHandler.

    This adapter is used by the legacy ``create_app()`` shim: it creates a
    ``SessionHandler`` per-request (with ``processors`` from the root context)
    and delegates to the named handler method.  The typed parameters
    (``BodyParam``, ``QueryParam``, ``MiddlewareParam``, etc.) are extracted
    from the ``web.Request`` in the same way ``_wrap_api_handler`` does.
    """
    method = getattr(SessionHandler, method_name)
    sig = inspect.signature(method, eval_str=True)

    async def _handler(request: web.Request) -> web.StreamResponse:
        root_ctx: RootContext = request.app["_root.context"]
        instance = SessionHandler(processors=root_ctx.processors)
        bound = getattr(instance, method_name)

        kwargs: dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            kwargs[name] = await extract_param_value(request, param.annotation)

        response = await bound(**kwargs)
        if isinstance(response, web.StreamResponse):
            return response
        return parse_response(response)

    return _handler
