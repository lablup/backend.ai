"""Route registry for REST v2 export endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.export.handler import ExportHandler
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_export_routes(
    handler: ExportHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 export routes and return the sub-registry."""
    registry = RouteRegistry.create("export", route_deps.cors_options)

    # Report metadata
    registry.add(
        "GET",
        "/reports",
        handler.list_reports,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/reports/{report_key}",
        handler.get_report,
        middlewares=[superadmin_required],
    )

    # Admin CSV export (full scope)
    registry.add(
        "POST",
        "/users/csv",
        handler.export_users_csv,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/sessions/csv",
        handler.export_sessions_csv,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/projects/csv",
        handler.export_projects_csv,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/keypairs/csv",
        handler.export_keypairs_csv,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/audit-logs/csv",
        handler.export_audit_logs_csv,
        middlewares=[superadmin_required],
    )

    # Scoped CSV export
    registry.add(
        "POST",
        "/sessions/projects/{project_id}/csv",
        handler.export_sessions_by_project_csv,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/users/domains/{domain_name}/csv",
        handler.export_users_by_domain_csv,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/sessions/my/csv",
        handler.export_my_sessions_csv,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/keypairs/my/csv",
        handler.export_my_keypairs_csv,
        middlewares=[auth_required],
    )

    return registry
