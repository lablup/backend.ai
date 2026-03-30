"""
Request DTOs for keypair DTO v2.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.keypair.types import KeypairOrderField

__all__ = (
    "AdminCreateKeypairInput",
    "AdminDeleteKeypairInput",
    "AdminSearchKeypairsInput",
    "AdminUpdateKeypairInput",
    "KeypairFilter",
    "KeypairOrderBy",
    "RevokeMyKeypairInput",
    "SearchMyKeypairsRequest",
    "SwitchMyMainAccessKeyInput",
    "UpdateMyKeypairInput",
)


class KeypairFilter(BaseRequestModel):
    """Filter for keypair search."""

    is_active: bool | None = None
    is_admin: bool | None = None
    access_key: StringFilter | None = None
    resource_policy: StringFilter | None = None
    created_at: DateTimeFilter | None = None
    last_used: DateTimeFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


KeypairFilter.model_rebuild()


class KeypairOrderBy(BaseRequestModel):
    """Order by specification for keypairs."""

    field: KeypairOrderField
    direction: OrderDirection = OrderDirection.DESC


class SearchMyKeypairsRequest(BaseRequestModel):
    """Search input for current user's keypairs. Shared by GQL and REST."""

    filter: KeypairFilter | None = Field(default=None, description="Filter conditions.")
    order: list[KeypairOrderBy] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor-based: return first N items.")
    after: str | None = Field(default=None, description="Cursor-based: return items after cursor.")
    last: int | None = Field(default=None, description="Cursor-based: return last N items.")
    before: str | None = Field(
        default=None, description="Cursor-based: return items before cursor."
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Offset-based: maximum items to return.",
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of items to skip."
    )


class RevokeMyKeypairInput(BaseRequestModel):
    """Request to revoke a keypair owned by the current user."""

    access_key: str = Field(description="Access key of the keypair to revoke.")


class UpdateMyKeypairInput(BaseRequestModel):
    """Request to update a keypair owned by the current user."""

    access_key: str = Field(description="Access key of the keypair to update.")
    is_active: bool = Field(description="New active state for the keypair.")


class SwitchMyMainAccessKeyInput(BaseRequestModel):
    """Request to switch the main access key for the current user."""

    access_key: str = Field(description="Access key to set as the new main key.")


class AdminCreateKeypairInput(BaseRequestModel):
    """Admin request to create a keypair for a target user."""

    user_id: UUID = Field(description="UUID of the target user.")
    resource_policy: str = Field(description="Name of the resource policy to assign.")
    is_active: bool = Field(default=True, description="Whether the keypair should be active.")
    is_admin: bool = Field(default=False, description="Whether the keypair has admin privileges.")
    rate_limit: int = Field(default=30000, description="API rate limit (requests per minute).")


class AdminUpdateKeypairInput(BaseRequestModel):
    """Admin request to update a keypair."""

    access_key: str = Field(description="Access key of the keypair to update.")
    is_active: bool | None = Field(default=None, description="New active state.")
    is_admin: bool | None = Field(default=None, description="New admin privilege state.")
    resource_policy: str | None = Field(default=None, description="New resource policy name.")
    rate_limit: int | None = Field(default=None, description="New API rate limit.")


class AdminDeleteKeypairInput(BaseRequestModel):
    """Admin request to delete a keypair."""

    access_key: str = Field(description="Access key of the keypair to delete.")


class AdminSearchKeypairsInput(BaseRequestModel):
    """Admin search input for keypairs. Shared by GQL and REST."""

    filter: KeypairFilter | None = Field(default=None, description="Filter conditions.")
    order: list[KeypairOrderBy] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor-based: return first N items.")
    after: str | None = Field(default=None, description="Cursor-based: return items after cursor.")
    last: int | None = Field(default=None, description="Cursor-based: return last N items.")
    before: str | None = Field(
        default=None, description="Cursor-based: return items before cursor."
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Offset-based: maximum items to return.",
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of items to skip."
    )
