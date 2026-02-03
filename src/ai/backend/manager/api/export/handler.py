"""
REST API handlers for CSV export system.
Provides endpoints for listing reports and report metadata.

Report-specific CSV export handlers are in separate modules:
- users.py: POST /export/users/csv
- sessions.py: POST /export/sessions/csv
- projects.py: POST /export/projects/csv
- keypairs.py: POST /export/keypairs/csv
- audit_logs.py: POST /export/audit-logs/csv
"""

from __future__ import annotations

from collections.abc import Iterable
from http import HTTPStatus

import aiohttp_cors
from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    PathParam,
    api_handler,
)
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.export import (
    ExportFieldInfo,
    ExportReportInfo,
    GetExportReportResponse,
    ListExportReportsResponse,
)
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.api.types import CORSOptions, WebMiddleware
from ai.backend.manager.dto.context import ProcessorsCtx
from ai.backend.manager.dto.export import ExportPathParam
from ai.backend.manager.services.export.actions import (
    GetReportAction,
    ListReportsAction,
)

from .audit_logs import AuditLogExportHandler
from .keypairs import KeypairExportHandler
from .projects import ProjectExportHandler
from .sessions import SessionExportHandler
from .users import UserExportHandler

__all__ = ("create_app",)


class ExportAPIHandler:
    """REST API handler class for CSV export metadata operations.

    Handles listing and getting report metadata.
    Report-specific CSV export is handled by dedicated handlers.
    """

    @auth_required_for_method
    @api_handler
    async def list_reports(
        self,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """List available export reports."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can access export reports.")

        # Call service through processors
        action_result = await processors_ctx.processors.export.list_reports.wait_for_complete(
            ListReportsAction()
        )

        # Convert to response DTO
        reports = [
            ExportReportInfo(
                report_key=r.report_key,
                name=r.name,
                description=r.description,
                fields=[
                    ExportFieldInfo(
                        key=f.key,
                        name=f.name,
                        description=f.description,
                        field_type=f.field_type.value,
                    )
                    for f in r.fields
                ],
            )
            for r in action_result.reports
        ]

        resp = ListExportReportsResponse(reports=reports)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def get_report(
        self,
        path: PathParam[ExportPathParam],
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get a specific export report by key."""
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can access export reports.")

        # Call service through processors
        action_result = await processors_ctx.processors.export.get_report.wait_for_complete(
            GetReportAction(report_key=path.parsed.report_key)
        )

        # Convert to response DTO
        report = action_result.report
        resp = GetExportReportResponse(
            report=ExportReportInfo(
                report_key=report.report_key,
                name=report.name,
                description=report.description,
                fields=[
                    ExportFieldInfo(
                        key=f.key,
                        name=f.name,
                        description=f.description,
                        field_type=f.field_type.value,
                    )
                    for f in report.fields
                ],
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    """Create aiohttp application for export API endpoints."""
    app = web.Application()
    app["api_versions"] = (4, 5)
    app["prefix"] = "export"

    cors = aiohttp_cors.setup(app, defaults=default_cors_options)

    # Common handlers for report metadata
    handler = ExportAPIHandler()
    cors.add(app.router.add_route("GET", "/reports", handler.list_reports))
    cors.add(app.router.add_route("GET", "/reports/{report_key}", handler.get_report))

    # Report-specific CSV export handlers
    user_handler = UserExportHandler()
    cors.add(app.router.add_route("POST", "/users/csv", user_handler.export_csv))

    session_handler = SessionExportHandler()
    cors.add(app.router.add_route("POST", "/sessions/csv", session_handler.export_csv))

    project_handler = ProjectExportHandler()
    cors.add(app.router.add_route("POST", "/projects/csv", project_handler.export_csv))

    keypair_handler = KeypairExportHandler()
    cors.add(app.router.add_route("POST", "/keypairs/csv", keypair_handler.export_csv))

    audit_log_handler = AuditLogExportHandler()
    cors.add(app.router.add_route("POST", "/audit-logs/csv", audit_log_handler.export_csv))

    return app, []
