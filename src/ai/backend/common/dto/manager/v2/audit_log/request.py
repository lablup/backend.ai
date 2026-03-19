"""Request DTOs for Audit Log DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter

from .types import AuditLogOrderField, AuditLogStatus, OrderDirection

__all__ = (
    "AdminSearchAuditLogsInput",
    "AuditLogFilter",
    "AuditLogOrder",
    "AuditLogStatusFilter",
)


class AuditLogStatusFilter(BaseRequestModel):
    """Filter for audit log status."""

    equals: AuditLogStatus | None = Field(default=None, description="Exact status match")
    in_: list[AuditLogStatus] | None = Field(
        default=None, alias="in", description="Status is in list"
    )
    not_in: list[AuditLogStatus] | None = Field(default=None, description="Status is not in list")


class AuditLogFilter(BaseRequestModel):
    """Filter for audit logs."""

    entity_type: StringFilter | None = Field(default=None, description="Entity type filter")
    operation: StringFilter | None = Field(default=None, description="Operation filter")
    status: AuditLogStatusFilter | None = Field(default=None, description="Status filter")
    triggered_by: StringFilter | None = Field(default=None, description="Triggered-by filter")
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter logs by created_at datetime"
    )
    AND: list[AuditLogFilter] | None = Field(default=None, description="All conditions must match")
    OR: list[AuditLogFilter] | None = Field(
        default=None, description="At least one condition must match"
    )
    NOT: list[AuditLogFilter] | None = Field(
        default=None, description="None of the conditions must match"
    )


AuditLogFilter.model_rebuild()


class AuditLogOrder(BaseRequestModel):
    """Ordering specification for audit logs."""

    field: AuditLogOrderField
    direction: OrderDirection = OrderDirection.DESC


class AdminSearchAuditLogsInput(BaseRequestModel):
    """Input for searching audit logs (admin, no scope)."""

    filter: AuditLogFilter | None = Field(default=None, description="Filter criteria")
    order: list[AuditLogOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")
