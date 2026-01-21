"""
Response DTOs for the CSV export system.

This module defines the response structures returned by the export API endpoints,
including lists of available reports and individual report details.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import ExportReportInfo

__all__ = (
    "GetExportReportResponse",
    "ListExportReportsResponse",
)


class ListExportReportsResponse(BaseResponseModel):
    """
    Response containing a list of all available export reports.

    Returned by GET /export/reports endpoint.
    Use this to discover what reports are available for export.
    """

    reports: list[ExportReportInfo] = Field(
        description=(
            "List of all available export reports. "
            "Each report includes its key (for use in export requests), "
            "name, description, and list of exportable fields."
        )
    )


class GetExportReportResponse(BaseResponseModel):
    """
    Response containing details of a single export report.

    Returned by GET /export/reports/{report_key} endpoint.
    Use this to get detailed information about a specific report
    before making an export request.
    """

    report: ExportReportInfo = Field(
        description=(
            "Detailed information about the requested report, "
            "including its metadata and all available fields for export."
        )
    )
