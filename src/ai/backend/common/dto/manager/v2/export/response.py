"""
Response DTOs for the CSV export system (v2).

This module defines the response structures returned by the export API v2 endpoints,
including lists of available reports and individual report details.

Unlike the v1 models, these use canonical snake_case field names with no camelCase aliases.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.export.types import ExportReportInfoNode

__all__ = (
    "GetExportReportPayload",
    "ListExportReportsPayload",
)


class ListExportReportsPayload(BaseResponseModel):
    """
    Payload containing a list of all available export reports.

    Returned by GET /v2/export/reports endpoint.
    Use this to discover what reports are available for export.
    """

    reports: list[ExportReportInfoNode] = Field(
        description=(
            "List of all available export reports. "
            "Each report includes its key (for use in export requests), "
            "name, description, and list of exportable fields."
        )
    )


class GetExportReportPayload(BaseResponseModel):
    """
    Payload containing details of a single export report.

    Returned by GET /v2/export/reports/{report_key} endpoint.
    Use this to get detailed information about a specific report
    before making an export request.
    """

    report: ExportReportInfoNode = Field(
        description=(
            "Detailed information about the requested report, "
            "including its metadata and all available fields for export."
        )
    )
