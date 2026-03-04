"""Export module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_export_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the export sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import ExportHandler

    reg = RouteRegistry.create("export", deps.cors_options)
    reg.app["_export_repository"] = deps.export_repository
    reg.app["_export_config"] = deps.export_config
    handler = ExportHandler(processors=deps.processors)

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
