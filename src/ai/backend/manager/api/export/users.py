"""
REST API handler for User CSV export.
"""

from __future__ import annotations

from http import HTTPStatus

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIStreamResponse,
    BodyParam,
    HeaderParam,
    stream_api_handler,
)
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.export import UserExportCSVRequest
from ai.backend.manager.api.auth import auth_required_for_method
from ai.backend.manager.dto.context import ExportCtx, ProcessorsCtx
from ai.backend.manager.dto.export import ExportFilenameHeader
from ai.backend.manager.exporter.csv import CSVExporter
from ai.backend.manager.exporter.stream import CSVExportStreamReader
from ai.backend.manager.repositories.base.export import ExportDataStream
from ai.backend.manager.services.export.actions import ExportUsersCSVAction

from .adapter import ExportAdapter

__all__ = ("UserExportHandler",)

USERS_REPORT_KEY = "users"


class UserExportHandler:
    """REST API handler for user CSV export operations."""

    def __init__(self) -> None:
        self._adapter = ExportAdapter()

    @auth_required_for_method
    @stream_api_handler
    async def export_csv(
        self,
        body: BodyParam[UserExportCSVRequest],
        header: HeaderParam[ExportFilenameHeader],
        processors_ctx: ProcessorsCtx,
        export_ctx: ExportCtx,
    ) -> APIStreamResponse:
        """Export user data as CSV.

        POST /export/users/csv
        """
        me = current_user()
        if me is None or not me.is_superadmin:
            raise web.HTTPForbidden(reason="Only superadmin can export data.")

        # Get report definition from repository
        report = export_ctx.repository.get_report(USERS_REPORT_KEY)

        # Build query using adapter
        query = self._adapter.build_user_query(
            report=report,
            fields=body.parsed.fields,
            filter=body.parsed.filter,
            order=body.parsed.order,
            max_rows=export_ctx.config.max_rows,
            statement_timeout_sec=export_ctx.config.statement_timeout_sec,
        )

        # Create action with pre-built query
        action = ExportUsersCSVAction(
            query=query,
            encoding=body.parsed.encoding,
            filename=header.parsed.filename,
        )

        # Call service through processors
        action_result = await processors_ctx.processors.export.export_users_csv.wait_for_complete(
            action
        )

        # Create CSV exporter and stream reader
        data_stream = ExportDataStream(
            field_names=action_result.field_names,
            reader=action_result.row_iterator,
        )
        exporter = CSVExporter(data_stream, encoding=action_result.encoding)
        stream_reader = CSVExportStreamReader(exporter)

        # Build response headers
        headers = {
            "Content-Disposition": f'attachment; filename="{action_result.filename}"',
            "Content-Type": f"text/csv; charset={action_result.encoding}",
        }

        return APIStreamResponse(body=stream_reader, status=HTTPStatus.OK, headers=headers)
