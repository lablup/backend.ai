"""Common types for Audit Log DTO v2."""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "AuditLogOrderField",
    "AuditLogStatus",
    "OrderDirection",
)


class AuditLogStatus(StrEnum):
    """Status of an audit log entry."""

    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"


class AuditLogOrderField(StrEnum):
    """Fields available for ordering audit logs."""

    CREATED_AT = "created_at"
    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    STATUS = "status"


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"
