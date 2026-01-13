"""Audit log export report definition."""

from __future__ import annotations

from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    ExportFieldType,
    ReportDef,
)

# Field definitions for audit log export
AUDIT_LOG_FIELDS: list[ExportFieldDef] = [
    ExportFieldDef(
        key="id",
        name="ID",
        description="Unique identifier of the audit log entry",
        field_type=ExportFieldType.UUID,
        column=AuditLogRow.id,
    ),
    ExportFieldDef(
        key="action_id",
        name="Action ID",
        description="ID of the action that triggered this log",
        field_type=ExportFieldType.UUID,
        column=AuditLogRow.action_id,
    ),
    ExportFieldDef(
        key="entity_type",
        name="Entity Type",
        description="Type of entity affected (e.g., session, user)",
        field_type=ExportFieldType.STRING,
        column=AuditLogRow.entity_type,
    ),
    ExportFieldDef(
        key="entity_id",
        name="Entity ID",
        description="ID of the affected entity",
        field_type=ExportFieldType.STRING,
        column=AuditLogRow.entity_id,
    ),
    ExportFieldDef(
        key="operation",
        name="Operation",
        description="Type of operation performed",
        field_type=ExportFieldType.STRING,
        column=AuditLogRow.operation,
    ),
    ExportFieldDef(
        key="status",
        name="Status",
        description="Operation status (success, failure, etc.)",
        field_type=ExportFieldType.ENUM,
        column=AuditLogRow.status,
        formatter=lambda v: str(v) if v else "",
    ),
    ExportFieldDef(
        key="created_at",
        name="Created At",
        description="Timestamp when the log was created",
        field_type=ExportFieldType.DATETIME,
        column=AuditLogRow.created_at,
        formatter=lambda v: v.isoformat() if v else "",
    ),
    ExportFieldDef(
        key="description",
        name="Description",
        description="Human-readable description of the action",
        field_type=ExportFieldType.STRING,
        column=AuditLogRow.description,
    ),
    ExportFieldDef(
        key="request_id",
        name="Request ID",
        description="ID of the API request that triggered this action",
        field_type=ExportFieldType.STRING,
        column=AuditLogRow.request_id,
    ),
    ExportFieldDef(
        key="triggered_by",
        name="Triggered By",
        description="User or system that triggered this action",
        field_type=ExportFieldType.STRING,
        column=AuditLogRow.triggered_by,
    ),
    ExportFieldDef(
        key="duration",
        name="Duration",
        description="Duration of the operation",
        field_type=ExportFieldType.STRING,
        column=AuditLogRow.duration,
        formatter=lambda v: str(v) if v else "",
    ),
]


# Report definition
AUDIT_LOG_REPORT = ReportDef(
    report_key="audit-logs",
    name="Audit Logs",
    description="System audit log records for compliance and monitoring",
    select_from=AuditLogRow.__table__,
    fields=AUDIT_LOG_FIELDS,
)
