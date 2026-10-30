"""Request DTOs for system session environ DTO v2."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.environ.types import ENVIRON_KEY_PATTERN
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    EnumFilter,
    NullableDateTimeFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironOrderField,
    SystemSessionEnvironScope,
    SystemSessionEnvironScopeType,
)
from ai.backend.common.tristate.unset import UNSET, Unset

__all__ = (
    "AdminSearchSystemSessionEnvironsInput",
    "CreateSystemSessionEnvironInput",
    "MySearchSystemSessionEnvironsInput",
    "ScopedSearchSystemSessionEnvironsInput",
    "SystemSessionEnvironFilter",
    "SystemSessionEnvironOrder",
    "SystemSessionEnvironScopeTypeFilter",
    "SystemSessionEnvironValueSourceFilter",
    "UpdateSystemSessionEnvironInput",
)


class SystemSessionEnvironValueSourceFilter(BaseRequestModel):
    """Filter by value source name. The names are strings so that a new value source does not
    change the schema."""

    equals: str | None = Field(default=None, description="Exact match.")
    in_: list[str] | None = Field(
        default=None, alias="in", description="Match any of the provided values."
    )
    not_equals: str | None = Field(default=None, description="Exclude an exact match.")
    not_in: list[str] | None = Field(
        default=None, description="Exclude any of the provided values."
    )


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
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by when the row was created."
    )
    updated_at: DateTimeFilter | None = Field(
        default=None, description="Filter by when the row was last changed."
    )
    deleted_at: NullableDateTimeFilter | None = Field(
        default=None, description="Filter by when the row was soft-deleted."
    )
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


class MySearchSystemSessionEnvironsInput(BaseRequestModel):
    """Input for searching the rows bound to public, the caller's domain and the projects the
    caller belongs to, soft-deleted ones excluded."""

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


class CreateSystemSessionEnvironInput(BaseRequestModel):
    """Input for binding a value source to an environment variable name at one scope."""

    key: str = Field(
        max_length=256,
        pattern=ENVIRON_KEY_PATTERN,
        description="The environment variable name the value is injected under.",
    )
    value_source: str = Field(
        description=(
            "Which value of the starting session is injected, as a value source name "
            "the value source query lists."
        )
    )
    scope_type: SystemSessionEnvironScopeType = Field(
        description="Whether the row applies to every session, a domain's or a project's."
    )
    scope_id: SystemSessionEnvironScopeID | None = Field(
        default=None,
        description="The id of the domain or the project. Left out for public.",
    )

    @model_validator(mode="after")
    def _validate_scope_id_for_scope_type(self) -> Self:
        if (self.scope_type is SystemSessionEnvironScopeType.PUBLIC) != (self.scope_id is None):
            raise ValueError("scope_id is left out for public and given for domain and project")
        return self


class UpdateSystemSessionEnvironInput(BaseRequestModel):
    """Input for changing a system session environ row's key."""

    key: (
        Annotated[str, StringConstraints(max_length=256, pattern=ENVIRON_KEY_PATTERN)]
        | None
        | Unset
    ) = Field(default=UNSET, description="New environment variable name. Omit to leave unchanged.")
