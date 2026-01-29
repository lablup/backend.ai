"""
Request DTOs for Session export report.

This module defines the filter, order, and request structures specific to session data export,
including filters for session name, type, status, access key, and timestamps.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

from .types import OrderDirection

__all__ = (
    "SessionExportFilter",
    "SessionExportOrder",
    "SessionExportOrderField",
    "SessionExportCSVRequest",
)


class SessionExportOrderField(StrEnum):
    """
    Orderable fields for session export.

    These are the fields that can be used for sorting session export results.
    Includes both creation and termination timestamps for flexible time-based ordering.
    """

    NAME = "name"
    SESSION_TYPE = "session_type"
    DOMAIN_NAME = "domain_name"
    ACCESS_KEY = "access_key"
    STATUS = "status"
    SCALING_GROUP_NAME = "scaling_group_name"
    CLUSTER_SIZE = "cluster_size"
    CREATED_AT = "created_at"
    TERMINATED_AT = "terminated_at"


class SessionExportOrder(BaseRequestModel):
    """
    Specifies how to sort the exported session data.

    Multiple SessionExportOrder instances can be provided to define multi-level sorting.
    The order in the list determines priority (first item is primary sort key).
    """

    field: SessionExportOrderField = Field(
        description=(
            "The field to sort by. Must be one of the valid session orderable fields: "
            "name, session_type, domain_name, access_key, status, scaling_group_name, "
            "cluster_size, created_at, terminated_at."
        )
    )
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description=(
            "Sort direction. 'asc' for ascending (A-Z, oldest-first), "
            "'desc' for descending (Z-A, newest-first). Default is 'asc'."
        ),
    )


class SessionExportFilter(BaseRequestModel):
    """
    Filter conditions specific to session export.

    All specified conditions are combined with AND logic.
    Only records matching all specified filters will be exported.
    Use this to narrow down the exported session data to specific criteria.
    """

    name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter sessions by name. Supports various match modes: "
            "contains, equals, starts_with, ends_with. "
            "Can be case-insensitive and/or negated."
        ),
    )
    session_type: list[str] | None = Field(
        default=None,
        description=(
            "Filter sessions by type(s). Accepts a list of type values "
            "(e.g., ['interactive', 'batch', 'inference']). Uses IN query."
        ),
    )
    domain_name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter sessions by domain name. "
            "Use this to export sessions belonging to a specific domain."
        ),
    )
    access_key: StringFilter | None = Field(
        default=None,
        description=(
            "Filter sessions by the owning access key. "
            "Use this to export sessions created by a specific user/keypair."
        ),
    )
    status: list[str] | None = Field(
        default=None,
        description=(
            "Filter sessions by status(es). Accepts a list of status values "
            "(e.g., ['PENDING', 'RUNNING', 'TERMINATED']). Uses IN query."
        ),
    )
    scaling_group_name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter sessions by scaling group name. "
            "Use this to export sessions running on specific resource pools."
        ),
    )
    created_at: DateTimeRangeFilter | None = Field(
        default=None,
        description=(
            "Filter sessions by creation timestamp. "
            "Specify 'after' and/or 'before' to define the datetime range. "
            "Useful for exporting sessions created within a specific period."
        ),
    )
    terminated_at: DateTimeRangeFilter | None = Field(
        default=None,
        description=(
            "Filter sessions by termination timestamp. "
            "Specify 'after' and/or 'before' to define the datetime range. "
            "Useful for exporting sessions that ended within a specific period. "
            "Note: Only terminated sessions have this field populated."
        ),
    )


class SessionExportCSVRequest(BaseRequestModel):
    """
    Request body for session CSV export operations.

    This is the request model for POST /export/sessions/csv endpoint.
    All parameters are optional to allow flexible export configurations.
    """

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available fields: id, name, session_type, domain_name, access_key, status, "
            "status_info, scaling_group_name, cluster_size, occupying_slots, created_at, terminated_at. "
            "If not specified or empty, all available fields will be exported."
        ),
    )
    filter: SessionExportFilter | None = Field(
        default=None,
        description=(
            "Filter conditions to apply before export. "
            "Only sessions matching all specified conditions will be included. "
            "If not specified, all sessions (up to max_rows limit) will be exported."
        ),
    )
    order: list[SessionExportOrder] | None = Field(
        default=None,
        description=(
            "List of ordering specifications for sorting the exported data. "
            "Multiple orders can be specified for multi-level sorting. "
            "The first item in the list is the primary sort key."
        ),
    )
    encoding: str = Field(
        default="utf-8",
        description=(
            "Character encoding for the CSV output. "
            "Supported values: 'utf-8' (default, recommended for most uses), "
            "'euc-kr' (for Korean systems requiring legacy encoding)."
        ),
    )
