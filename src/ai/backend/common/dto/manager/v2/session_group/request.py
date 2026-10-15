"""
Request DTOs for SessionGroup v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    EnumFilter,
    NullableDateTimeFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupOrderField,
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
    SessionGroupScope,
)

__all__ = (
    "AdminSearchSessionGroupsInput",
    "ScopedSearchSessionGroupsInput",
    "SessionGroupFilter",
    "SessionGroupOrder",
)


class SessionGroupFilter(BaseRequestModel):
    """Filter for session groups.

    Groups marked deleted are left out unless the top-level filter gives ``deleted_at``.
    A ``deleted_at`` inside ``AND``/``OR``/``NOT`` does not lift that default.
    """

    entity_id: UUIDFilter | None = Field(default=None, description="Filter by session group ID.")
    domain_id: UUIDFilter | None = Field(default=None, description="Filter by domain ID.")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID.")
    owner_user_id: UUIDFilter | None = Field(
        default=None, description="Filter by the ID of the owning user."
    )
    placement_direction: EnumFilter[SessionGroupPlacementDirectionEnum] | None = Field(
        default=None, description="Filter by placement direction."
    )
    placement_enforcement: EnumFilter[SessionGroupPlacementEnforcementEnum] | None = Field(
        default=None, description="Filter by placement enforcement."
    )
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    deleted_at: NullableDateTimeFilter | None = Field(
        default=None,
        description=(
            "Filter by deletion time. Setting it on the top-level filter includes the groups "
            "marked deleted; inside AND, OR or NOT it does not."
        ),
    )

    AND: list[SessionGroupFilter] | None = Field(
        default=None, description="AND logical combinator."
    )
    OR: list[SessionGroupFilter] | None = Field(default=None, description="OR logical combinator.")
    NOT: list[SessionGroupFilter] | None = Field(
        default=None, description="NOT logical combinator."
    )


SessionGroupFilter.model_rebuild()


class SessionGroupOrder(BaseRequestModel):
    """Order specification for session groups."""

    field: SessionGroupOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ScopedSearchSessionGroupsInput(BaseRequestModel):
    """Input for searching session groups within scopes."""

    scope: SessionGroupScope = Field(description="Scope (OR across all items).")
    filter: SessionGroupFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SessionGroupOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class AdminSearchSessionGroupsInput(BaseRequestModel):
    """Input for searching every session group (superadmin)."""

    filter: SessionGroupFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SessionGroupOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
