"""Export handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``PathParam``, ``HeaderParam``, etc.)
are automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` or ``web.StreamResponse`` objects.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Sequence
from http import HTTPStatus
from typing import Any, Final, Protocol

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    HeaderParam,
    PathParam,
)
from ai.backend.common.dto.manager.v2.export import (
    AuditLogExportCSVInput,
    ExportFieldInfoNode,
    ExportReportInfoNode,
    GetExportReportPayload,
    KeypairExportCSVInput,
    ListExportReportsPayload,
    ProjectExportCSVInput,
    SessionExportCSVInput,
    UserExportCSVInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.unified import ExportConfig
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.dto.export import (
    ExportDomainPathParam,
    ExportFilenameHeader,
    ExportPathParam,
    ExportProjectPathParam,
)
from ai.backend.manager.exporter.csv import CSVExporter
from ai.backend.manager.exporter.stream import CSVExportStreamReader
from ai.backend.manager.repositories.base.export import ExportDataStream
from ai.backend.manager.services.export.actions import (
    ExportAuditLogsCSVAction,
    ExportKeypairsCSVAction,
    ExportMyKeypairsCSVAction,
    ExportMySessionsCSVAction,
    ExportProjectsCSVAction,
    ExportSessionsByProjectCSVAction,
    ExportSessionsCSVAction,
    ExportUsersByDomainCSVAction,
    ExportUsersCSVAction,
    GetReportAction,
    ListReportsAction,
)
from ai.backend.manager.services.export.processors import ExportProcessors

from .adapter import ExportAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class _CSVExportResult(Protocol):
    """Structural type shared by all CSV export action results."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str


USERS_REPORT_KEY = "users"
SESSIONS_REPORT_KEY = "sessions"
PROJECTS_REPORT_KEY = "projects"
KEYPAIRS_REPORT_KEY = "keypairs"
AUDIT_LOGS_REPORT_KEY = "audit-logs"


class ExportHandler:
    """Export API handler with constructor-injected dependencies."""

    def __init__(self, *, export: ExportProcessors, export_config: ExportConfig) -> None:
        self._export = export
        self._adapter = ExportAdapter()
        self._export_config = export_config

    # ------------------------------------------------------------------
    # list_reports (GET /export/reports)
    # ------------------------------------------------------------------

    async def list_reports(self) -> APIResponse:
        """List available export reports."""
        action_result = await self._export.list_reports.wait_for_complete(ListReportsAction())

        reports = [
            ExportReportInfoNode(
                report_key=r.report_key,
                name=r.name,
                description=r.description,
                fields=[
                    ExportFieldInfoNode(
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

        resp = ListExportReportsPayload(reports=reports)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # ------------------------------------------------------------------
    # get_report (GET /export/reports/{report_key})
    # ------------------------------------------------------------------

    async def get_report(
        self,
        path: PathParam[ExportPathParam],
    ) -> APIResponse:
        """Get a specific export report by key."""
        action_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=path.parsed.report_key)
        )

        report = action_result.report
        resp = GetExportReportPayload(
            report=ExportReportInfoNode(
                report_key=report.report_key,
                name=report.name,
                description=report.description,
                fields=[
                    ExportFieldInfoNode(
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

    # ------------------------------------------------------------------
    # export_users_csv (POST /export/users/csv)
    # ------------------------------------------------------------------

    async def export_users_csv(
        self,
        body: BodyParam[UserExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export user data as CSV."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=USERS_REPORT_KEY)
        )
        query = self._adapter.build_user_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportUsersCSVAction(
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_users_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_sessions_csv (POST /export/sessions/csv)
    # ------------------------------------------------------------------

    async def export_sessions_csv(
        self,
        body: BodyParam[SessionExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export session data as CSV."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=SESSIONS_REPORT_KEY)
        )
        query = self._adapter.build_session_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportSessionsCSVAction(
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_sessions_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_projects_csv (POST /export/projects/csv)
    # ------------------------------------------------------------------

    async def export_projects_csv(
        self,
        body: BodyParam[ProjectExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export project data as CSV."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=PROJECTS_REPORT_KEY)
        )
        query = self._adapter.build_project_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportProjectsCSVAction(
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_projects_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_keypairs_csv (POST /export/keypairs/csv)
    # ------------------------------------------------------------------

    async def export_keypairs_csv(
        self,
        body: BodyParam[KeypairExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export keypair data as CSV."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=KEYPAIRS_REPORT_KEY)
        )
        query = self._adapter.build_keypair_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=None,
            order=None,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportKeypairsCSVAction(
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_keypairs_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_audit_logs_csv (POST /export/audit-logs/csv)
    # ------------------------------------------------------------------

    async def export_audit_logs_csv(
        self,
        body: BodyParam[AuditLogExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export audit log data as CSV."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=AUDIT_LOGS_REPORT_KEY)
        )
        query = self._adapter.build_audit_log_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportAuditLogsCSVAction(
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_audit_logs_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_sessions_by_project_csv
    # (POST /export/sessions/projects/{project_id}/csv)
    # ------------------------------------------------------------------

    async def export_sessions_by_project_csv(
        self,
        body: BodyParam[SessionExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        path: PathParam[ExportProjectPathParam],
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export session data as CSV scoped to a project."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=SESSIONS_REPORT_KEY)
        )
        query = self._adapter.build_session_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportSessionsByProjectCSVAction(
            project_id=path.parsed.project_id,
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_sessions_by_project_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_users_by_domain_csv
    # (POST /export/users/domains/{domain_name}/csv)
    # ------------------------------------------------------------------

    async def export_users_by_domain_csv(
        self,
        body: BodyParam[UserExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        path: PathParam[ExportDomainPathParam],
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export user data as CSV scoped to a domain."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=USERS_REPORT_KEY)
        )
        query = self._adapter.build_user_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportUsersByDomainCSVAction(
            domain_name=path.parsed.domain_name,
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_users_by_domain_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_my_sessions_csv (POST /export/sessions/my/csv)
    # ------------------------------------------------------------------

    async def export_my_sessions_csv(
        self,
        body: BodyParam[SessionExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        user_ctx: UserContext,
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export session data as CSV scoped to the current user."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=SESSIONS_REPORT_KEY)
        )
        query = self._adapter.build_session_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportMySessionsCSVAction(
            user_uuid=user_ctx.user_uuid,
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_my_sessions_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # export_my_keypairs_csv (POST /export/keypairs/my/csv)
    # ------------------------------------------------------------------

    async def export_my_keypairs_csv(
        self,
        body: BodyParam[KeypairExportCSVInput],
        header: HeaderParam[ExportFilenameHeader],
        user_ctx: UserContext,
        request_ctx: RequestCtx,
    ) -> web.StreamResponse:
        """Export keypair data as CSV scoped to the current user."""
        report_result = await self._export.get_report.wait_for_complete(
            GetReportAction(report_key=KEYPAIRS_REPORT_KEY)
        )
        query = self._adapter.build_keypair_query(
            report=report_result.report,
            fields=body.parsed.fields,
            filter=None,
            order=None,
            max_rows=self._export_config.max_rows,
            statement_timeout_sec=self._export_config.statement_timeout_sec,
        )
        action = ExportMyKeypairsCSVAction(
            user_uuid=user_ctx.user_uuid,
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )
        action_result = await self._export.export_my_keypairs_csv.wait_for_complete(action)
        return await self._build_csv_stream_response(request_ctx.request, action_result)

    # ------------------------------------------------------------------
    # Shared streaming helper
    # ------------------------------------------------------------------

    @staticmethod
    async def _build_csv_stream_response(
        request: web.Request,
        action_result: _CSVExportResult,
    ) -> web.StreamResponse:
        """Build a streaming CSV response from an export action result.

        Replicates the streaming logic from the old ``@stream_api_handler``
        decorator so that this handler works with ``_wrap_api_handler``.
        """
        data_stream = ExportDataStream(
            field_names=action_result.field_names,
            reader=action_result.row_iterator,
        )
        exporter = CSVExporter(data_stream, encoding=action_result.encoding)
        stream_reader = CSVExportStreamReader(exporter)

        headers = {
            "Content-Disposition": f'attachment; filename="{action_result.filename}"',
            "Content-Type": f"text/csv; charset={action_result.encoding}",
        }

        resp = web.StreamResponse(status=HTTPStatus.OK, headers=headers)
        body_iter = stream_reader.read()

        try:
            first_chunk = await body_iter.__anext__()
            await resp.prepare(request)
            await resp.write(first_chunk)
        except Exception as e:
            raise web.HTTPInternalServerError(
                reason=f"Failed to send first chunk from stream: {e!r}"
            ) from e

        try:
            async for chunk in body_iter:
                await resp.write(chunk)
            await resp.write_eof()
        except Exception:
            log.exception("Error during streaming response body iteration")
            resp.force_close()

        return resp
