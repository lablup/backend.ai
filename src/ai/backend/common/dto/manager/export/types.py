"""
Common types for the CSV export system.

This module defines shared data types used across the export API,
including order directions, field metadata, report information, and report keys.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "ExportFieldInfo",
    "ExportReportInfo",
    "ExportReportKey",
    "OrderDirection",
)


class ExportReportKey(StrEnum):
    """
    Available export report keys.

    These are the valid values for identifying export reports.
    Each key corresponds to a specific data domain that can be exported.
    """

    USERS = "users"
    SESSIONS = "sessions"
    PROJECTS = "projects"


class OrderDirection(StrEnum):
    """
    Specifies the direction for sorting export results.

    Used in ExportOrder to control whether results are sorted
    in ascending or descending order for each field.
    """

    ASC = "asc"
    DESC = "desc"


class ExportFieldInfo(BaseRequestModel):
    """
    Describes a single exportable field within a report.

    Each field represents a column that can be included in the CSV export.
    Fields can be selectively included or excluded when making export requests.
    """

    key: str = Field(
        description=(
            "Unique identifier for this field within the report. "
            "Use this key when specifying which fields to include in an export request."
        )
    )
    name: str = Field(
        description=(
            "Human-readable display name for the field. "
            "This name is used as the column header in the exported CSV."
        )
    )
    description: str = Field(
        description=(
            "Detailed description explaining what data this field contains "
            "and any relevant context for interpreting its values."
        )
    )
    field_type: str = Field(
        description=(
            "Data type of the field values. Common types include: "
            "'string', 'integer', 'datetime', 'boolean', 'uuid', 'json'. "
            "This helps clients understand how to parse and display the values."
        )
    )


class ExportReportInfo(BaseRequestModel):
    """
    Provides metadata about an available export report.

    A report defines a specific data domain (e.g., users, sessions, projects)
    that can be exported to CSV. Each report has a unique key and contains
    a list of fields that can be included in the export.
    """

    report_key: str = Field(
        description=(
            "Unique identifier for this report. "
            "Use this key in the export endpoint URL to request this specific report. "
            "Example values: 'users', 'sessions', 'projects', 'audit_logs'."
        )
    )
    name: str = Field(
        description=(
            "Human-readable name for the report, suitable for display in UIs. "
            "Example: 'User Accounts', 'Compute Sessions', 'Projects'."
        )
    )
    description: str = Field(
        description=(
            "Detailed description of what data this report contains and its intended use. "
            "Helps users understand which report to choose for their export needs."
        )
    )
    fields: list[ExportFieldInfo] = Field(
        description=(
            "List of all fields available in this report. "
            "Each field can be selectively included or excluded when making export requests. "
            "If no fields are specified in a request, all fields are exported by default."
        )
    )
