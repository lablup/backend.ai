"""Request DTOs for Audit Log DTO v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

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
    created_at_before: datetime | None = Field(
        default=None, description="Filter logs created before this timestamp"
    )
    created_at_after: datetime | None = Field(
        default=None, description="Filter logs created after this timestamp"
    )


class AuditLogOrder(BaseRequestModel):
    """Ordering specification for audit logs."""

    field: AuditLogOrderField
    direction: OrderDirection = OrderDirection.DESC


class AdminSearchAuditLogsInput(BaseRequestModel):
    """Input for searching audit logs (admin, no scope)."""

    filter: AuditLogFilter | None = Field(default=None, description="Filter criteria")
    order: list[AuditLogOrder] | None = Field(default=None, description="Sort order")
    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")
