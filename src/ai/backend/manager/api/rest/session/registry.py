"""Session module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import SessionHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_session_routes(handler: SessionHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the session sub-application."""

    reg = RouteRegistry.create("session", route_deps.cors_options)

    # --- Session creation ---
    reg.add(
        "POST",
        "",
        handler.create_from_params,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "POST",
        "/_/create",
        handler.create_from_params,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "POST",
        "/_/create-from-template",
        handler.create_from_template,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "POST",
        "/_/create-cluster",
        handler.create_cluster,
        middlewares=[route_deps.all_status_mw, auth_required],
    )

    # --- Session matching / utilities ---
    reg.add(
        "GET",
        "/_/match",
        handler.match_sessions,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        "/_/sync-agent-registry",
        handler.sync_agent_registry,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "POST",
        "/_/transit-status",
        handler.check_and_transit_status,
        middlewares=[auth_required, route_deps.all_status_mw],
    )

    # --- Task logs ---
    reg.add(
        "HEAD",
        "/_/logs",
        handler.get_task_logs,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "GET",
        "/_/logs",
        handler.get_task_logs,
        middlewares=[route_deps.read_status_mw, auth_required],
    )

    # --- Per-session CRUD ---
    reg.add(
        "GET",
        r"/{session_name}",
        handler.get_info,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "PATCH",
        r"/{session_name}",
        handler.restart,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "DELETE",
        r"/{session_name}",
        handler.destroy,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}",
        handler.execute,
        middlewares=[route_deps.read_status_mw, auth_required],
    )

    # --- Per-session sub-resources ---
    reg.add(
        "GET",
        r"/{session_name}/direct-access-info",
        handler.get_direct_access_info,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/logs",
        handler.get_container_logs,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/rename",
        handler.rename_session,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/interrupt",
        handler.interrupt,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/complete",
        handler.complete,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/shutdown-service",
        handler.shutdown_service,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/upload",
        handler.upload_files,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/download",
        handler.download_files,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/download_single",
        handler.download_single,
        middlewares=[auth_required, route_deps.read_status_mw],
    )
    reg.add(
        "GET",
        r"/{session_name}/files",
        handler.list_files,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/start-service",
        handler.start_service,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/commit",
        handler.commit_session,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/imagify",
        handler.convert_session_to_image,
        middlewares=[auth_required, route_deps.all_status_mw],
    )
    reg.add(
        "GET",
        r"/{session_name}/commit",
        handler.get_commit_status,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/status-history",
        handler.get_status_history,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/abusing-report",
        handler.get_abusing_report,
        middlewares=[route_deps.all_status_mw, auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/dependency-graph",
        handler.get_dependency_graph,
        middlewares=[route_deps.read_status_mw, auth_required],
    )
    return reg
