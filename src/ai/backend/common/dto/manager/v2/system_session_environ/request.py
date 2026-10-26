"""Request DTOs for system session environ DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import EnumFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironOrderField,
    SystemSessionEnvironScope,
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)

__all__ = (
    "AdminSearchSystemSessionEnvironsInput",
    "ScopedSearchSystemSessionEnvironsInput",
    "SystemSessionEnvironFilter",
    "SystemSessionEnvironOrder",
    "SystemSessionEnvironScopeTypeFilter",
    "SystemSessionEnvironValueSourceFilter",
)


class SystemSessionEnvironValueSourceFilter(EnumFilter[SystemSessionEnvironValueSource]):
    """Filter for the value of a starting session a row injects."""


class SystemSessionEnvironScopeTypeFilter(EnumFilter[SystemSessionEnvironScopeType]):
    """Filter for whether a row applies to every session, a domain's or a project's."""


class SystemSessionEnvironFilter(BaseRequestModel):
    entity_id: UUIDFilter | None = Field(default=None, description="Filter by the row's id.")
    key: StringFilter | None = Field(
        default=None, description="Filter by the environment variable name."
    )
    value_source: SystemSessionEnvironValueSourceFilter | None = Field(
        default=None, description="Filter by which value of the starting session is injected."
    )
    scope_type: SystemSessionEnvironScopeTypeFilter | None = Field(
        default=None, description="Filter by the kind of scope the row is bound to."
    )
    scope_id: UUIDFilter | None = Field(
        default=None,
        description="Filter by the id of the public entity, the domain or the project.",
    )
    enabled: bool | None = Field(default=None, description="Filter by the enabled flag.")
    AND: list[SystemSessionEnvironFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[SystemSessionEnvironFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[SystemSessionEnvironFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


SystemSessionEnvironFilter.model_rebuild()


class SystemSessionEnvironOrder(BaseRequestModel):
    field: SystemSessionEnvironOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchSystemSessionEnvironsInput(BaseRequestModel):
    """Input for searching every system session environ row (superadmin)."""

    filter: SystemSessionEnvironFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[SystemSessionEnvironOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, ge=1, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, ge=1, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, ge=0, description="Offset pagination: number to skip.")


class ScopedSearchSystemSessionEnvironsInput(BaseRequestModel):
    """Input for searching the system session environ rows the named scopes reach."""

    scope: SystemSessionEnvironScope = Field(description="Scope (OR across all items).")
    filter: SystemSessionEnvironFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[SystemSessionEnvironOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, ge=1, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, ge=1, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, ge=0, description="Offset pagination: number to skip.")
