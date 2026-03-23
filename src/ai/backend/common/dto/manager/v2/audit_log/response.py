"""Response DTOs for Audit Log DTO v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import AuditLogStatus

__all__ = (
    "AdminSearchAuditLogsPayload",
    "AuditLogNode",
)


class AuditLogNode(BaseResponseModel):
    """Node model representing an audit log entry."""

    id: UUID = Field(description="Audit log entry ID")
    action_id: UUID = Field(description="UUID of the action that generated this log")
    entity_type: str = Field(description="Type of entity this log relates to")
    operation: str = Field(description="Operation performed")
    entity_id: str | None = Field(default=None, description="ID of the affected entity")
    created_at: datetime = Field(description="Timestamp when the audit log was created")
    request_id: str | None = Field(default=None, description="Request ID that triggered this")
    triggered_by: str | None = Field(
        default=None, description="UUID string of the user who triggered the action"
    )
    description: str = Field(description="Human-readable description of the operation")
    duration: str | None = Field(default=None, description="Duration of the operation as a string")
    status: AuditLogStatus = Field(description="Status of the operation")


class AdminSearchAuditLogsPayload(BaseResponseModel):
    """Payload for audit log search result."""

    items: list[AuditLogNode] = Field(description="Audit log list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
