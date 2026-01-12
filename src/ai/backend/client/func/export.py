"""Client SDK functions for CSV export system."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Optional

from ai.backend.client.request import Request
from ai.backend.common.dto.manager.export import (
    AuditLogExportCSVRequest,
    AuditLogExportFilter,
    AuditLogExportOrder,
    GetExportReportResponse,
    ListExportReportsResponse,
    ProjectExportCSVRequest,
    ProjectExportFilter,
    ProjectExportOrder,
    SessionExportCSVRequest,
    SessionExportFilter,
    SessionExportOrder,
    UserExportCSVRequest,
    UserExportFilter,
    UserExportOrder,
)

from .base import BaseFunction, api_function

__all__ = ("Export",)


class Export(BaseFunction):
    """
    Provides functions to interact with the CSV export system.
    Supports listing available reports and streaming report-specific CSV exports.
    """

    @api_function
    @classmethod
    async def list_reports(cls) -> ListExportReportsResponse:
        """
        List all available export reports.

        :returns: List of available export reports with their fields
        """
        rqst = Request("GET", "/export/reports")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListExportReportsResponse.model_validate(data)

    @api_function
    @classmethod
    async def get_report(cls, report_key: str) -> GetExportReportResponse:
        """
        Get a specific export report by key.

        :param report_key: The report key (e.g., 'sessions', 'users', 'projects')
        :returns: Report details including available fields
        """
        rqst = Request("GET", f"/export/reports/{report_key}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetExportReportResponse.model_validate(data)

    # =========================================================================
    # User Export
    # =========================================================================

    @api_function
    @classmethod
    async def stream_users_csv(
        cls,
        *,
        fields: Optional[list[str]] = None,
        filter: Optional[UserExportFilter] = None,
        order: Optional[list[UserExportOrder]] = None,
        encoding: str = "utf-8",
        filename: Optional[str] = None,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Stream user export as an async iterator of chunks.

        :param fields: Optional list of field keys to include (default: all fields)
        :param filter: Optional user-specific filter conditions
        :param order: Optional list of user order specifications
        :param encoding: CSV encoding (default: utf-8, also supports euc-kr)
        :param filename: Optional filename for the export
        :param chunk_size: Size of chunks to yield (default: 8192 bytes)
        :yields: Chunks of CSV data as bytes
        """
        request = UserExportCSVRequest(
            fields=fields,
            filter=filter,
            order=order,
            encoding=encoding,
        )

        rqst = Request("POST", "/export/users/csv")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        if filename:
            rqst.headers["X-Export-Filename"] = filename

        async with rqst.fetch() as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    # =========================================================================
    # Session Export
    # =========================================================================

    @api_function
    @classmethod
    async def stream_sessions_csv(
        cls,
        *,
        fields: Optional[list[str]] = None,
        filter: Optional[SessionExportFilter] = None,
        order: Optional[list[SessionExportOrder]] = None,
        encoding: str = "utf-8",
        filename: Optional[str] = None,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Stream session export as an async iterator of chunks.

        :param fields: Optional list of field keys to include (default: all fields)
        :param filter: Optional session-specific filter conditions
        :param order: Optional list of session order specifications
        :param encoding: CSV encoding (default: utf-8, also supports euc-kr)
        :param filename: Optional filename for the export
        :param chunk_size: Size of chunks to yield (default: 8192 bytes)
        :yields: Chunks of CSV data as bytes
        """
        request = SessionExportCSVRequest(
            fields=fields,
            filter=filter,
            order=order,
            encoding=encoding,
        )

        rqst = Request("POST", "/export/sessions/csv")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        if filename:
            rqst.headers["X-Export-Filename"] = filename

        async with rqst.fetch() as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    # =========================================================================
    # Project Export
    # =========================================================================

    @api_function
    @classmethod
    async def stream_projects_csv(
        cls,
        *,
        fields: Optional[list[str]] = None,
        filter: Optional[ProjectExportFilter] = None,
        order: Optional[list[ProjectExportOrder]] = None,
        encoding: str = "utf-8",
        filename: Optional[str] = None,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Stream project export as an async iterator of chunks.

        :param fields: Optional list of field keys to include (default: all fields)
        :param filter: Optional project-specific filter conditions
        :param order: Optional list of project order specifications
        :param encoding: CSV encoding (default: utf-8, also supports euc-kr)
        :param filename: Optional filename for the export
        :param chunk_size: Size of chunks to yield (default: 8192 bytes)
        :yields: Chunks of CSV data as bytes
        """
        request = ProjectExportCSVRequest(
            fields=fields,
            filter=filter,
            order=order,
            encoding=encoding,
        )

        rqst = Request("POST", "/export/projects/csv")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        if filename:
            rqst.headers["X-Export-Filename"] = filename

        async with rqst.fetch() as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    # =========================================================================
    # Audit Log Export
    # =========================================================================

    @api_function
    @classmethod
    async def stream_audit_logs_csv(
        cls,
        *,
        fields: Optional[list[str]] = None,
        filter: Optional[AuditLogExportFilter] = None,
        order: Optional[list[AuditLogExportOrder]] = None,
        encoding: str = "utf-8",
        filename: Optional[str] = None,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Stream audit log export as an async iterator of chunks.

        :param fields: Optional list of field keys to include (default: all fields)
        :param filter: Optional audit log-specific filter conditions
        :param order: Optional list of audit log order specifications
        :param encoding: CSV encoding (default: utf-8, also supports euc-kr)
        :param filename: Optional filename for the export
        :param chunk_size: Size of chunks to yield (default: 8192 bytes)
        :yields: Chunks of CSV data as bytes
        """
        request = AuditLogExportCSVRequest(
            fields=fields,
            filter=filter,
            order=order,
            encoding=encoding,
        )

        rqst = Request("POST", "/export/audit-logs/csv")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        if filename:
            rqst.headers["X-Export-Filename"] = filename

        async with rqst.fetch() as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk
