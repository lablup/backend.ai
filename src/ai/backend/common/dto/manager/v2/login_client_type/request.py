"""Request DTOs for login_client_type v2."""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import NonEmptyList, String64
from ai.backend.common.dto.manager.v2.login_client_type.types import (
    LoginClientTypeOrderField,
    OrderDirection,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.tristate.unset import UNSET, Unset

__all__ = (
    "SearchLoginClientTypesInput",
    "CreateLoginClientTypeInput",
    "LoginClientTypeFilter",
    "LoginClientTypeOrder",
    "PartialBulkPurgeLoginClientTypesInput",
    "PartialBulkUpdateLoginClientTypeItemInput",
    "PartialBulkUpdateLoginClientTypesInput",
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

    Every field defaults to UNSET (no change). ``description`` accepts ``null`` to clear.
    """

    name: String64 | None | Unset = Field(
        default=UNSET,
        description="Updated name. Omit to leave unchanged.",
    )
    description: str | None | Unset = Field(
        default=UNSET,
        description="Updated description. Omit to leave unchanged; null clears.",
    )


class PartialBulkUpdateLoginClientTypeItemInput(BaseRequestModel):
    """One login client type of a partial bulk update and the fields to update on it."""

    id: UUID = Field(description="ID of the login client type to update.")
    input: UpdateLoginClientTypeInput = Field(
        description="Fields to update on the login client type."
    )


class PartialBulkUpdateLoginClientTypesInput(BaseRequestModel):
    """Input for updating several login client types, each answered for separately."""

    items: NonEmptyList[PartialBulkUpdateLoginClientTypeItemInput] = Field(
        description="The login client types to update, each with its fields."
    )


class PartialBulkPurgeLoginClientTypesInput(BaseRequestModel):
    """Input for purging several login client types, each answered for separately."""

    ids: NonEmptyList[UUID] = Field(description="IDs of the login client types to purge.")


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
    entity_id: UUIDFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Filter by login client type ID.",
    )
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


LoginClientTypeFilter.model_rebuild()


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
