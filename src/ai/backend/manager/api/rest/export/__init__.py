"""New-style export module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ExportHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register export routes on the given RouteRegistry."""
    handler = ExportHandler(processors=processors)

    # Report metadata endpoints
    registry.add(
        "GET",
        "/export/reports",
        handler.list_reports,
        middlewares=[auth_required, superadmin_required],
    )
    registry.add(
        "GET",
        "/export/reports/{report_key}",
        handler.get_report,
        middlewares=[auth_required, superadmin_required],
    )

    # CSV export endpoints
    registry.add(
        "POST",
        "/export/users/csv",
        handler.export_users_csv,
        middlewares=[auth_required, superadmin_required],
    )
    registry.add(
        "POST",
        "/export/sessions/csv",
        handler.export_sessions_csv,
        middlewares=[auth_required, superadmin_required],
    )
    registry.add(
        "POST",
        "/export/projects/csv",
        handler.export_projects_csv,
        middlewares=[auth_required, superadmin_required],
    )
    registry.add(
        "POST",
        "/export/keypairs/csv",
        handler.export_keypairs_csv,
        middlewares=[auth_required, superadmin_required],
    )
    registry.add(
        "POST",
        "/export/audit-logs/csv",
        handler.export_audit_logs_csv,
        middlewares=[auth_required, superadmin_required],
    )
