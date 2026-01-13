"""User export report definition."""

from __future__ import annotations

from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    ReportDef,
)

# Field definitions for user export
USER_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="uuid",
        name="UUID",
        description="User UUID",
        field_type=ExportFieldType.UUID,
        column=UserRow.uuid,
    ),
    ExportFieldDef(
        key="username",
        name="Username",
        description="Login username",
        field_type=ExportFieldType.STRING,
        column=UserRow.username,
    ),
    ExportFieldDef(
        key="email",
        name="Email",
        description="Email address",
        field_type=ExportFieldType.STRING,
        column=UserRow.email,
    ),
    ExportFieldDef(
        key="full_name",
        name="Full Name",
        description="User full name",
        field_type=ExportFieldType.STRING,
        column=UserRow.full_name,
    ),
    ExportFieldDef(
        key="domain_name",
        name="Domain",
        description="Domain name",
        field_type=ExportFieldType.STRING,
        column=UserRow.domain_name,
    ),
    ExportFieldDef(
        key="role",
        name="Role",
        description="User role",
        field_type=ExportFieldType.ENUM,
        column=UserRow.role,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="status",
        name="Status",
        description="User status",
        field_type=ExportFieldType.ENUM,
        column=UserRow.status,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Registration time",
        field_type=ExportFieldType.DATETIME,
        column=UserRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="modified_at",
        name="Modified At",
        description="Last modification time",
        field_type=ExportFieldType.DATETIME,
        column=UserRow.modified_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
]


# Report definition
USER_REPORT = ReportDef(
    report_key="users",
    name="Users",
    description="User account export report",
    select_from=UserRow.__table__,
    fields=USER_FIELDS,
)
