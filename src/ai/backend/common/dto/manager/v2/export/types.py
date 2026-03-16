"""
Common types for the CSV export DTO v2.

Defines shared enums and sub-models used across the export API v2,
including order directions, report keys, field metadata, and boolean filters.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel

__all__ = (
    "BooleanFilter",
    "ExportFieldInfoNode",
    "ExportReportInfoNode",
    "ExportReportKey",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Specifies the direction for sorting export results."""

    ASC = "asc"
    DESC = "desc"


class ExportReportKey(StrEnum):
    """Available export report keys identifying each exportable data domain."""

    USERS = "users"
    SESSIONS = "sessions"
    PROJECTS = "projects"


class ExportFieldInfoNode(BaseResponseModel):
    """Describes a single exportable field within a report."""

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
            "'string', 'integer', 'datetime', 'boolean', 'uuid', 'json'."
        )
    )


class ExportReportInfoNode(BaseResponseModel):
    """Provides metadata about an available export report."""

    report_key: str = Field(
        description=(
            "Unique identifier for this report. "
            "Use this key in the export endpoint URL to request this specific report."
        )
    )
    name: str = Field(
        description="Human-readable name for the report, suitable for display in UIs."
    )
    description: str = Field(
        description="Detailed description of what data this report contains and its intended use."
    )
    fields: list[ExportFieldInfoNode] = Field(
        description=(
            "List of all fields available in this report. "
            "Each field can be selectively included or excluded when making export requests."
        )
    )


class BooleanFilter(BaseRequestModel):
    """Filter for boolean fields. Matches records where the field equals the specified value."""

    equals: bool = Field(
        description=(
            "The boolean value to match. "
            "Set to true to include only records where the field is true, "
            "or false to include only records where the field is false."
        )
    )
