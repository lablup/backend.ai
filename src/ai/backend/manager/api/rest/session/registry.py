"""Session module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import (
    ALL_ALLOWED,
    READ_ALLOWED,
    server_status_required,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_session_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the session sub-application."""
    from .handler import SessionHandler

    reg = RouteRegistry.create("session", deps.cors_options)
    handler = SessionHandler(processors=deps.processors, config_provider=deps.config_provider)

    # --- Session creation ---
    reg.add(
        "POST",
        "",
        handler.create_from_params,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        "/_/create",
        handler.create_from_params,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        "/_/create-from-template",
        handler.create_from_template,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        "/_/create-cluster",
        handler.create_cluster,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )

    # --- Session matching / utilities ---
    reg.add(
        "GET",
        "/_/match",
        handler.match_sessions,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        "/_/sync-agent-registry",
        handler.sync_agent_registry,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        "/_/transit-status",
        handler.check_and_transit_status,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED, deps.config_provider)],
    )

    # --- Task logs ---
    reg.add(
        "HEAD",
        "/_/logs",
        handler.get_task_logs,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "GET",
        "/_/logs",
        handler.get_task_logs,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )

    # --- Per-session CRUD ---
    reg.add(
        "GET",
        r"/{session_name}",
        handler.get_info,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "PATCH",
        r"/{session_name}",
        handler.restart,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "DELETE",
        r"/{session_name}",
        handler.destroy,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}",
        handler.execute,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )

    # --- Per-session sub-resources ---
    reg.add(
        "GET",
        r"/{session_name}/direct-access-info",
        handler.get_direct_access_info,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/logs",
        handler.get_container_logs,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/rename",
        handler.rename_session,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/interrupt",
        handler.interrupt,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/complete",
        handler.complete,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/shutdown-service",
        handler.shutdown_service,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/upload",
        handler.upload_files,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/download",
        handler.download_files,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/download_single",
        handler.download_single,
        middlewares=[auth_required, server_status_required(READ_ALLOWED, deps.config_provider)],
    )
    reg.add(
        "GET",
        r"/{session_name}/files",
        handler.list_files,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/start-service",
        handler.start_service,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/commit",
        handler.commit_session,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "POST",
        r"/{session_name}/imagify",
        handler.convert_session_to_image,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED, deps.config_provider)],
    )
    reg.add(
        "GET",
        r"/{session_name}/commit",
        handler.get_commit_status,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/status-history",
        handler.get_status_history,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/abusing-report",
        handler.get_abusing_report,
        middlewares=[server_status_required(ALL_ALLOWED, deps.config_provider), auth_required],
    )
    reg.add(
        "GET",
        r"/{session_name}/dependency-graph",
        handler.get_dependency_graph,
        middlewares=[server_status_required(READ_ALLOWED, deps.config_provider), auth_required],
    )
    return reg
