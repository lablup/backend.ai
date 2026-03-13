"""Export module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ExportHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_export_routes(handler: ExportHandler, route_deps: RouteDeps) -> RouteRegistry:
    """Build the export sub-application."""

    reg = RouteRegistry.create("export", route_deps.cors_options)

    # Report metadata endpoints
    reg.add(
        "GET",
        "/reports",
        handler.list_reports,
        middlewares=[auth_required, superadmin_required],
    )
    reg.add(
        "GET",
        "/reports/{report_key}",
        handler.get_report,
        middlewares=[auth_required, superadmin_required],
    )

    # CSV export endpoints
    reg.add(
        "POST",
        "/users/csv",
        handler.export_users_csv,
        middlewares=[auth_required, superadmin_required],
    )
    reg.add(
        "POST",
        "/sessions/csv",
        handler.export_sessions_csv,
        middlewares=[auth_required, superadmin_required],
    )
    reg.add(
        "POST",
        "/projects/csv",
        handler.export_projects_csv,
        middlewares=[auth_required, superadmin_required],
    )
    reg.add(
        "POST",
        "/keypairs/csv",
        handler.export_keypairs_csv,
        middlewares=[auth_required, superadmin_required],
    )
    reg.add(
        "POST",
        "/audit-logs/csv",
        handler.export_audit_logs_csv,
        middlewares=[auth_required, superadmin_required],
    )
    return reg
