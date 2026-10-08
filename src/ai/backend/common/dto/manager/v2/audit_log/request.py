"""Request DTOs for Audit Log DTO v2."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.rbac.types import EntityTypeScope, UUIDScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

from .types import (
    AuditLogActionKind,
    AuditLogOrderField,
    AuditLogScopeOrderField,
    AuditLogStatus,
    OrderDirection,
)

__all__ = (
    "AdminSearchAuditLogsInput",
    "AuditLogActionKindFilter",
    "AuditLogFilter",
    "AuditLogOrder",
    "AuditLogScope",
    "AuditLogScopeFilter",
    "AuditLogScopeOrder",
    "AuditLogStatusFilter",
    "ScopedSearchAuditLogsInput",
    "SearchAuditLogScopesInput",
)


class AuditLogStatusFilter(BaseRequestModel):
    """Filter for audit log status."""

    equals: AuditLogStatus | None = Field(default=None, description="Exact status match")
    in_: list[AuditLogStatus] | None = Field(
        default=None, alias="in", description="Status is in list"
    )
    not_equals: AuditLogStatus | None = Field(
        default=None, description="Excludes exact status match"
    )
    not_in: list[AuditLogStatus] | None = Field(default=None, description="Status is not in list")


class AuditLogActionKindFilter(BaseRequestModel):
    """Filter for audit log action kind."""

    equals: AuditLogActionKind | None = Field(default=None, description="Exact action kind match")
    in_: list[AuditLogActionKind] | None = Field(
        default=None, alias="in", description="Action kind is in list"
    )
    not_equals: AuditLogActionKind | None = Field(
        default=None, description="Excludes exact action kind match"
    )
    not_in: list[AuditLogActionKind] | None = Field(
        default=None, description="Action kind is not in list"
    )


class AuditLogFilter(BaseRequestModel):
    """Filter for audit logs."""

    entity_type: StringFilter | None = Field(default=None, description="Entity type filter")
    entity_id: StringFilter | None = Field(
        default=None,
        description=(
            f"Entity ID filter. Deprecated since {NEXT_RELEASE_VERSION}; use "
            "`target_entity_id`, which matches the id as a UUID."
        ),
        deprecated=True,
    )
    target_entity_id: UUIDFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Entity ID filter.",
    )
    operation: StringFilter | None = Field(default=None, description="Operation filter")
    status: AuditLogStatusFilter | None = Field(default=None, description="Status filter")
    triggered_by: StringFilter | None = Field(default=None, description="Triggered-by filter")
    acted_as: UUIDFilter | None = Field(
        default=None, description="Acted-as (effective/acting user UUID) filter"
    )
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter logs by created_at datetime"
    )
    action_name: StringFilter | None = Field(default=None, description="Action name filter")
    action_kind: AuditLogActionKindFilter | None = Field(
        default=None, description="Action kind filter"
    )
    lookup_kind: StringFilter | None = Field(default=None, description="Lookup kind filter")
    lookup_key: StringFilter | None = Field(default=None, description="Lookup key filter")
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


class AuditLogScope(BaseRequestModel):
    """Scope for the scoped audit log query.

    Each category list is OR'd internally and across categories. Raises an error
    if every field is empty.
    """

    entity: list[EntityTypeScope] | None = Field(
        default=None, description="Entity-tagged scope items"
    )
    triggered_user: list[UUIDScope] | None = Field(
        default=None, description="Actor UUIDs (matches audit_logs.triggered_by)"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> Self:
        if not self.entity and not self.triggered_user:
            raise ValueError(
                "AuditLogScope requires a non-empty value for 'entity' or 'triggered_user'"
            )
        return self


class ScopedSearchAuditLogsInput(BaseRequestModel):
    """Input for searching audit logs under a non-admin scope."""

    scope: AuditLogScope = Field(description="Scope (OR across all items)")
    filter: AuditLogFilter | None = Field(default=None, description="Filter criteria")
    order: list[AuditLogOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")


class AuditLogScopeFilter(BaseRequestModel):
    """Filter for the scopes of an audit log."""

    scope_type: StringFilter | None = Field(default=None, description="Scope type filter")
    scope_id: UUIDFilter | None = Field(default=None, description="Scope ID filter")


class AuditLogScopeOrder(BaseRequestModel):
    """Ordering specification for the scopes of an audit log."""

    field: AuditLogScopeOrderField
    direction: OrderDirection = OrderDirection.ASC


class SearchAuditLogScopesInput(BaseRequestModel):
    """Input for searching the scopes of one audit log."""

    filter: AuditLogScopeFilter | None = Field(default=None, description="Filter criteria")
    order: list[AuditLogScopeOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")
