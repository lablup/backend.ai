"""
Input DTOs for domain-specific CSV export requests (v2).

Defines per-domain order field enums, order models, filter models, and CSV input models
for User, Session, Project, AuditLog, and Keypair export operations.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter
from ai.backend.common.dto.manager.v2.export.types import BooleanFilter, OrderDirection

__all__ = (
    "AuditLogExportCSVInput",
    "AuditLogExportFilter",
    "AuditLogExportOrder",
    "AuditLogExportOrderField",
    "KeypairExportCSVInput",
    "ProjectExportCSVInput",
    "ProjectExportFilter",
    "ProjectExportOrder",
    "ProjectExportOrderField",
    "SessionExportCSVInput",
    "SessionExportFilter",
    "SessionExportOrder",
    "SessionExportOrderField",
    "UserExportCSVInput",
    "UserExportFilter",
    "UserExportOrder",
    "UserExportOrderField",
)


# ---------------------------------------------------------------------------
# User export
# ---------------------------------------------------------------------------


class UserExportOrderField(StrEnum):
    """Orderable fields for user export."""

    USERNAME = "username"
    EMAIL = "email"
    FULL_NAME = "full_name"
    DOMAIN_NAME = "domain_name"
    ROLE = "role"
    STATUS = "status"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"


class UserExportOrder(BaseRequestModel):
    """Specifies how to sort the exported user data."""

    field: UserExportOrderField = Field(
        description=(
            "The field to sort by. Must be one of the valid user orderable fields: "
            "username, email, full_name, domain_name, role, status, created_at, modified_at."
        )
    )
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description=(
            "Sort direction. 'asc' for ascending (A-Z, oldest-first), "
            "'desc' for descending (Z-A, newest-first). Default is 'asc'."
        ),
    )


class UserExportFilter(BaseRequestModel):
    """Filter conditions specific to user export. All conditions are combined with AND logic."""

    username: StringFilter | None = Field(
        default=None,
        description=(
            "Filter users by username. Supports various match modes: "
            "contains, equals, starts_with, ends_with. "
            "Can be case-insensitive and/or negated."
        ),
    )
    email: StringFilter | None = Field(
        default=None,
        description=(
            "Filter users by email address. Supports various match modes: "
            "contains, equals, starts_with, ends_with. "
            "Useful for finding users from specific email domains."
        ),
    )
    domain_name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter users by their assigned domain name. "
            "Use this to export users belonging to a specific domain."
        ),
    )
    role: list[str] | None = Field(
        default=None,
        description=(
            "Filter users by role(s). Accepts a list of role values "
            "(e.g., ['admin', 'user', 'monitor']). Uses IN query."
        ),
    )
    status: list[str] | None = Field(
        default=None,
        description=(
            "Filter users by account status(es). Accepts a list of status values "
            "(e.g., ['active', 'inactive']). Uses IN query."
        ),
    )
    created_at: DateTimeRangeFilter | None = Field(
        default=None,
        description=(
            "Filter users by their registration timestamp. "
            "Specify 'after' and/or 'before' to define the datetime range. "
            "Useful for exporting users registered within a specific period."
        ),
    )


class UserExportCSVInput(BaseRequestModel):
    """Input body for user CSV export operations (POST /export/users/csv)."""

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available fields: uuid, username, email, full_name, domain_name, role, status, "
            "created_at, modified_at. "
            "If not specified or empty, all available fields will be exported."
        ),
    )
    filter: UserExportFilter | None = Field(
        default=None,
        description=(
            "Filter conditions to apply before export. "
            "Only users matching all specified conditions will be included. "
            "If not specified, all users (up to max_rows limit) will be exported."
        ),
    )
    order: list[UserExportOrder] | None = Field(
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


# ---------------------------------------------------------------------------
# Session export
# ---------------------------------------------------------------------------


class SessionExportOrderField(StrEnum):
    """Orderable fields for session export."""

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
    """Specifies how to sort the exported session data."""

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
    """Filter conditions specific to session export. All conditions are combined with AND logic."""

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


class SessionExportCSVInput(BaseRequestModel):
    """Input body for session CSV export operations (POST /export/sessions/csv)."""

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available fields: id, name, session_type, domain_name, access_key, status, "
            "status_info, scaling_group_name, cluster_size, occupying_slots, created_at, "
            "terminated_at. "
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


# ---------------------------------------------------------------------------
# Project export
# ---------------------------------------------------------------------------


class ProjectExportOrderField(StrEnum):
    """Orderable fields for project export."""

    NAME = "name"
    DOMAIN_NAME = "domain_name"
    IS_ACTIVE = "is_active"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"


class ProjectExportOrder(BaseRequestModel):
    """Specifies how to sort the exported project data."""

    field: ProjectExportOrderField = Field(
        description=(
            "The field to sort by. Only base project fields are supported: "
            "name, domain_name, is_active, created_at, modified_at. "
            "JOIN fields (resource_policy, scaling_group, container_registry) are not orderable."
        )
    )
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description=(
            "Sort direction. 'asc' for ascending (A-Z, oldest-first, false-first), "
            "'desc' for descending (Z-A, newest-first, true-first). Default is 'asc'."
        ),
    )


class ProjectExportFilter(BaseRequestModel):
    """Filter conditions specific to project export. All conditions are combined with AND logic."""

    name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter projects by name. Supports various match modes: "
            "contains, equals, starts_with, ends_with. "
            "Can be case-insensitive and/or negated."
        ),
    )
    domain_name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter projects by domain name. "
            "Use this to export projects belonging to a specific domain."
        ),
    )
    is_active: BooleanFilter | None = Field(
        default=None,
        description=(
            "Filter projects by active status. "
            "Set equals to true for active projects only, "
            "or false for inactive/archived projects only."
        ),
    )
    created_at: DateTimeRangeFilter | None = Field(
        default=None,
        description=(
            "Filter projects by creation timestamp. "
            "Specify 'after' and/or 'before' to define the datetime range. "
            "Useful for exporting projects created within a specific period."
        ),
    )


class ProjectExportCSVInput(BaseRequestModel):
    """Input body for project CSV export operations (POST /export/projects/csv)."""

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available fields: id, name, description, domain_name, is_active, "
            "total_resource_slots, created_at, modified_at, container_registry. "
            "If not specified or empty, all available fields will be exported."
        ),
    )
    filter: ProjectExportFilter | None = Field(
        default=None,
        description=(
            "Filter conditions to apply before export. "
            "Only projects matching all specified conditions will be included. "
            "If not specified, all projects (up to max_rows limit) will be exported."
        ),
    )
    order: list[ProjectExportOrder] | None = Field(
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


# ---------------------------------------------------------------------------
# Audit log export
# ---------------------------------------------------------------------------


class AuditLogExportOrderField(StrEnum):
    """Orderable fields for audit log export."""

    ENTITY_TYPE = "entity_type"
    ENTITY_ID = "entity_id"
    OPERATION = "operation"
    STATUS = "status"
    CREATED_AT = "created_at"
    TRIGGERED_BY = "triggered_by"


class AuditLogExportOrder(BaseRequestModel):
    """Specifies how to sort the exported audit log data."""

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
    """Filter conditions specific to audit log export. All conditions are combined with AND logic."""

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


class AuditLogExportCSVInput(BaseRequestModel):
    """Input body for audit log CSV export operations (POST /export/audit-logs/csv)."""

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


# ---------------------------------------------------------------------------
# Keypair export
# ---------------------------------------------------------------------------


class KeypairExportCSVInput(BaseRequestModel):
    """Input body for keypair CSV export operations (POST /export/keypairs/csv)."""

    fields: list[str] | None = Field(
        default=None,
        description=(
            "List of field keys to include in the export. "
            "Available basic fields: access_key, user_id, user_uuid, is_active, is_admin, "
            "created_at, modified_at, last_used, resource_policy_name. "
            "Available JOIN fields: user_*, resource_policy_*, resource_group_*, session_*. "
            "If not specified or empty, all available fields will be exported."
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
