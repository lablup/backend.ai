from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_session_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.api.rest.types import WebRequestHandler
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_session_module"]


def register_routes(registry: RouteRegistry, processors: Processors | None = None) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_session_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import SessionHandler

    if processors is None:
        raise RuntimeError("processors is required for session module")
    handler = SessionHandler(processors=processors)

    # --- Session creation ---
    registry.add(
        "POST",
        "",
        handler.create_from_params,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/_/create",
        handler.create_from_params,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/_/create-from-template",
        handler.create_from_template,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/_/create-cluster",
        handler.create_cluster,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )

    # --- Session matching / utilities ---
    registry.add(
        "GET",
        "/_/match",
        handler.match_sessions,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/_/sync-agent-registry",
        handler.sync_agent_registry,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        "/_/transit-status",
        handler.check_and_transit_status,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED)],
    )

    # --- Task logs ---
    registry.add(
        "HEAD",
        "/_/logs",
        handler.get_task_logs,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        "/_/logs",
        handler.get_task_logs,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )

    # --- Per-session CRUD ---
    registry.add(
        "GET",
        r"/{session_name}",
        handler.get_info,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "PATCH",
        r"/{session_name}",
        handler.restart,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "DELETE",
        r"/{session_name}",
        handler.destroy,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}",
        handler.execute,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )

    # --- Per-session sub-resources ---
    registry.add(
        "GET",
        r"/{session_name}/direct-access-info",
        handler.get_direct_access_info,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/{session_name}/logs",
        handler.get_container_logs,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/rename",
        handler.rename_session,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/interrupt",
        handler.interrupt,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/complete",
        handler.complete,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/shutdown-service",
        handler.shutdown_service,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/upload",
        handler.upload_files,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/download",
        handler.download_files,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/download_single",
        handler.download_single,
        middlewares=[auth_required, server_status_required(READ_ALLOWED)],
    )
    registry.add(
        "GET",
        r"/{session_name}/files",
        handler.list_files,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/start-service",
        handler.start_service,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/commit",
        handler.commit_session,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "POST",
        r"/{session_name}/imagify",
        handler.convert_session_to_image,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED)],
    )
    registry.add(
        "GET",
        r"/{session_name}/commit",
        handler.get_commit_status,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/{session_name}/status-history",
        handler.get_status_history,
        middlewares=[server_status_required(READ_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/{session_name}/abusing-report",
        handler.get_abusing_report,
        middlewares=[server_status_required(ALL_ALLOWED), auth_required],
    )
    registry.add(
        "GET",
        r"/{session_name}/dependency-graph",
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
    import inspect
    from typing import Any

    from aiohttp import web

    from ai.backend.common.api_handlers import extract_param_value, parse_response

    from .handler import SessionHandler

    method = getattr(SessionHandler, method_name)
    sig = inspect.signature(method, eval_str=True)

    async def _handler(request: web.Request) -> web.StreamResponse:
        root_ctx = request.app["_root.context"]
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
