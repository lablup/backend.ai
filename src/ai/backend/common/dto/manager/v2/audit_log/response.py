"""Response DTOs for Audit Log DTO v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

from .types import AuditLogActionKind, AuditLogStatus

__all__ = (
    "AuditLogNode",
    "AuditLogScopeEntryNode",
    "SearchAuditLogScopesPayload",
    "SearchAuditLogsPayload",
)


class AuditLogScopeEntryNode(BaseResponseModel):
    """A scope an audited run covered."""

    id: UUID = Field(description="Audit log scope entry ID")
    field_id: UUID = Field(description="UUID of the audit log scope record.")
    audit_log_id: UUID = Field(description="ID of the audit log the scope belongs to.")
    scope_type: str = Field(description="Entity type of the scope.")
    scope_id: UUID = Field(description="ID of the scope entity.")


class AuditLogNode(BaseResponseModel):
    """Node model representing an audit log entry."""

    id: UUID = Field(description="Audit log entry ID")
    field_id: UUID = Field(
        description="UUID of the audit log record. Added in 26.9.0.",
    )
    action_id: UUID = Field(description="UUID of the action that generated this log")
    action_name: str = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Name of the action that wrote this log.",
    )
    action_kind: AuditLogActionKind | None = Field(
        default=None,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Shape of the action that wrote this log. "
            "Null for a log written before the action kind was recorded."
        ),
    )
    lookup_kind: str | None = Field(
        default=None,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Kind of natural key a lookup action read. "
            "Null for other action kinds."
        ),
    )
    lookup_key: str | None = Field(
        default=None,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Natural key a lookup action read. "
            "Null for other action kinds."
        ),
    )
    entity_type: str | None = Field(
        default=None,
        description=(
            "Type of entity this log relates to. Null for an operation that names "
            "scopes and no entity kind, such as linking two entities."
        ),
    )
    operation: str = Field(description="Operation performed")
    entity_id: str | None = Field(
        default=None,
        description=(
            f"ID of the affected entity. Deprecated since {NEXT_RELEASE_VERSION}; use "
            "`target_entity_id`, which carries the id as a UUID."
        ),
        deprecated=True,
    )
    target_entity_id: UUID | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. ID of the affected entity.",
    )
    created_at: datetime = Field(description="Timestamp when the audit log was created")
    request_id: str | None = Field(default=None, description="Request ID that triggered this")
    triggered_by: str | None = Field(
        default=None, description="UUID string of the user who triggered the action"
    )
    acted_as: UUID | None = Field(
        default=None,
        description=(
            "UUID of the effective (acting) user the action ran as. "
            "Differs from triggered_by only while a super admin is impersonating a target."
        ),
    )
    description: str = Field(description="Human-readable description of the operation")
    duration: str | None = Field(default=None, description="Duration of the operation as a string")
    client_ip: str | None = Field(
        default=None,
        description=(
            "Added in 26.9.0. IP address of the request that produced this "
            "record, masked per the client IP masking policy. Null when the policy records "
            "none, or when the address was unavailable or unusable."
        ),
    )
    status: AuditLogStatus = Field(description="Status of the operation")


class SearchAuditLogsPayload(BaseResponseModel):
    """Payload for audit log search result."""

    items: list[AuditLogNode] = Field(description="Audit log list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class SearchAuditLogScopesPayload(BaseResponseModel):
    """Payload for the scope search of one audit log."""

    items: list[AuditLogScopeEntryNode] = Field(description="Scope list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
