"""
Request DTOs for Audit Log export report.

This module defines the filter, order, and request structures specific to audit log data export,
including filters for entity type, operation, status, triggered_by, and timestamps.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter

from .types import OrderDirection

__all__ = (
    "AuditLogExportFilter",
    "AuditLogExportOrder",
    "AuditLogExportOrderField",
    "AuditLogExportCSVRequest",
)


class AuditLogExportOrderField(StrEnum):
    """
    Orderable fields for audit log export.

    These are the fields that can be used for sorting audit log export results.
    """

    ENTITY_TYPE = "entity_type"
    ENTITY_ID = "entity_id"
    OPERATION = "operation"
    STATUS = "status"
    CREATED_AT = "created_at"
    TRIGGERED_BY = "triggered_by"


class AuditLogExportOrder(BaseRequestModel):
    """
    Specifies how to sort the exported audit log data.

    Multiple AuditLogExportOrder instances can be provided to define multi-level sorting.
    The order in the list determines priority (first item is primary sort key).
    """

    field: AuditLogExportOrderField = Field(
        description=(
            "The field to sort by. Must be one of the valid audit log orderable fields: "
            "entity_type, entity_id, operation, status, created_at, triggered_by."
        )
    )
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description=(
            "Sort direction. 'asc' for ascending (A-Z, oldest-first), "
            "'desc' for descending (Z-A, newest-first). Default is 'asc'."
        ),
    )


class AuditLogExportFilter(BaseRequestModel):
    """
    Filter conditions specific to audit log export.

    All specified conditions are combined with AND logic.
    Only records matching all specified filters will be exported.
    Use this to narrow down the exported audit log data to specific criteria.
    """

    entity_type: StringFilter | None = Field(
        default=None,
        description=(
            "Filter audit logs by entity type (e.g., 'session', 'user', 'keypair'). "
            "Use exact match (equals) to filter by specific entity type."
        ),
    )
    entity_id: StringFilter | None = Field(
        default=None,
        description=(
            "Filter audit logs by entity ID. Use this to export audit logs for a specific entity."
        ),
    )
    operation: StringFilter | None = Field(
        default=None,
        description=(
            "Filter audit logs by operation type (e.g., 'create', 'update', 'delete'). "
            "Use exact match (equals) to filter by specific operation."
        ),
    )
    status: list[str] | None = Field(
        default=None,
        description=(
            "Filter audit logs by status(es). Accepts a list of status values "
            "(e.g., ['success', 'failure']). Uses IN query."
        ),
    )
    triggered_by: StringFilter | None = Field(
        default=None,
        description=(
            "Filter audit logs by the user or system that triggered the action. "
            "Use this to export audit logs initiated by a specific actor."
        ),
    )
    request_id: StringFilter | None = Field(
        default=None,
        description=(
            "Filter audit logs by request ID. "
            "Use this to export audit logs for a specific API request."
        ),
    )
    created_at: DateTimeRangeFilter | None = Field(
        default=None,
        description=(
            "Filter audit logs by creation timestamp. "
            "Specify 'after' and/or 'before' to define the datetime range. "
            "Useful for exporting audit logs within a specific period."
        ),
    )


class AuditLogExportCSVRequest(BaseRequestModel):
    """
    Request body for audit log CSV export operations.

    This is the request model for POST /export/audit-logs/csv endpoint.
    All parameters are optional to allow flexible export configurations.
    """

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available fields: id, action_id, entity_type, entity_id, operation, status, "
            "created_at, description, request_id, triggered_by, duration. "
            "If not specified or empty, all available fields will be exported."
        ),
    )
    filter: AuditLogExportFilter | None = Field(
        default=None,
        description=(
            "Filter conditions to apply before export. "
            "Only audit logs matching all specified conditions will be included. "
            "If not specified, all audit logs (up to max_rows limit) will be exported."
        ),
    )
    order: list[AuditLogExportOrder] | None = Field(
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
