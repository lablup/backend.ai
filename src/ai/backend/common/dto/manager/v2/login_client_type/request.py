"""Request DTOs for login_client_type v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.login_client_type.types import (
    LoginClientTypeOrderField,
    OrderDirection,
)

__all__ = (
    "SearchLoginClientTypesInput",
    "CreateLoginClientTypeInput",
    "LoginClientTypeFilter",
    "LoginClientTypeOrder",
    "UpdateLoginClientTypeInput",
)


class CreateLoginClientTypeInput(BaseRequestModel):
    """Input for creating a new login client type."""

    name: str = Field(
        min_length=1,
        max_length=64,
        description="Unique login client type name (e.g. 'core', 'webui').",
    )
    description: str | None = Field(
        default=None,
        description="Optional free-text description shown to administrators.",
    )


class UpdateLoginClientTypeInput(BaseRequestModel):
    """Input for updating a login client type.

    Fields default to "no change". For ``description``, pass ``null`` to clear the
    existing value; omit the field (SENTINEL) to leave it untouched.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Updated name. Omit to leave unchanged.",
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated description. Use null to clear, omit to leave unchanged.",
    )


class LoginClientTypeFilter(BaseRequestModel):
    """Filter criteria for login client type search."""

    name: StringFilter | None = Field(default=None, description="Filter by name.")
    description: StringFilter | None = Field(default=None, description="Filter by description.")
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by creation datetime."
    )
    modified_at: DateTimeFilter | None = Field(
        default=None, description="Filter by last modification datetime."
    )


class LoginClientTypeOrder(BaseRequestModel):
    """Single ordering criterion for login client type search."""

    field: LoginClientTypeOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Sort direction.")


class SearchLoginClientTypesInput(BaseRequestModel):
    """Input for paginated login client type search."""

    filter: LoginClientTypeFilter | None = Field(default=None, description="Filter criteria.")
    order: list[LoginClientTypeOrder] | None = Field(default=None, description="Ordering criteria.")
    first: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items after cursor"
    )
    after: str | None = Field(default=None, description="Cursor-based: start cursor (exclusive)")
    last: int | None = Field(
        default=None, ge=1, description="Cursor-based: number of items before cursor"
    )
    before: str | None = Field(default=None, description="Cursor-based: end cursor (exclusive)")
    limit: int | None = Field(
        default=None, ge=1, description="Offset-based: maximum number of results."
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of results to skip."
    )
