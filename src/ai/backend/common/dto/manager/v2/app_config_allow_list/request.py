"""Request DTOs for app_config_allow_list v2."""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigAllowListOrderField,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.common import NonEmptyList, OrderDirection
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

__all__ = (
    "AppConfigAllowListFilter",
    "AppConfigAllowListOrder",
    "CreateAppConfigAllowListInput",
    "PartialBulkPurgeAppConfigAllowListsInput",
    "PartialBulkUpdateAppConfigAllowListsInput",
    "PurgeAppConfigAllowListInput",
    "SearchAppConfigAllowListInput",
    "UpdateAppConfigAllowListInput",
)


class CreateAppConfigAllowListInput(BaseRequestModel):
    """Input for registering a new app config allow-list entry."""

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Registered config name to gate (FK to app_config_definitions).",
    )
    scope_type: AppConfigScopeType = Field(
        description="Scope at which fragments may be written (public | domain | user)."
    )
    rank: int | None = Field(
        default=None,
        description=(
            "Merge rank applied to fragments under this entry (low to high; higher wins). "
            "Defaults to the scope type's default rank (public=100, domain=200, user=300)."
        ),
    )


class UpdateAppConfigAllowListInput(BaseRequestModel):
    """Input for updating an app config allow-list entry.

    Only ``rank`` is updatable — the identity pair (``config_name``, ``scope_type``)
    is immutable (purge and recreate to change it).
    """

    id: UUID = Field(description="App config allow-list entry id to update.")
    rank: int | None = Field(
        default=None,
        description=(
            "New merge rank applied to fragments under this entry (low to high; "
            "higher wins). Omit to leave unchanged."
        ),
    )


class PurgeAppConfigAllowListInput(BaseRequestModel):
    """Input for purging an app config allow-list entry."""

    id: UUID = Field(description="App config allow-list entry id to purge.")


class PartialBulkUpdateAppConfigAllowListsInput(BaseRequestModel):
    """Input for updating several allow-list entries, each answered for separately."""

    items: NonEmptyList[UpdateAppConfigAllowListInput] = Field(
        description="The allow-list entries to update, each with its id and fields."
    )


class PartialBulkPurgeAppConfigAllowListsInput(BaseRequestModel):
    """Input for purging several allow-list entries, each answered for separately."""

    ids: NonEmptyList[UUID] = Field(description="IDs of the allow-list entries to purge.")


class AppConfigAllowListFilter(BaseRequestModel):
    """Filter for app config allow-list search."""

    config_name: StringFilter | None = Field(default=None, description="Filter by config name.")
    scope_type: AppConfigScopeTypeFilter | None = Field(
        default=None, description="Filter by scope type."
    )
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by creation datetime."
    )
    updated_at: DateTimeFilter | None = Field(
        default=None, description="Filter by last update datetime."
    )
    entity_id: UUIDFilter | None = Field(
        default=None,
        description=f"Added in {NEXT_RELEASE_VERSION}. Filter by allow-list entry ID.",
    )
    AND: list[Self] | None = Field(default=None, description="Match all of the given sub-filters.")
    OR: list[Self] | None = Field(default=None, description="Match any of the given sub-filters.")
    NOT: list[Self] | None = Field(default=None, description="Negate the given sub-filters.")


AppConfigAllowListFilter.model_rebuild()


class AppConfigAllowListOrder(BaseRequestModel):
    """Order specifier for app config allow-list search."""

    field: AppConfigAllowListOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchAppConfigAllowListInput(BaseRequestModel):
    """Input for paginated app config allow-list search."""

    filter: AppConfigAllowListFilter | None = Field(default=None, description="Filter conditions.")
    order: list[AppConfigAllowListOrder] | None = Field(
        default=None, description="Order specifiers, applied in sequence."
    )
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size.")
    after: str | None = Field(default=None, description="Cursor-forward start cursor.")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size.")
    before: str | None = Field(default=None, description="Cursor-backward end cursor.")
    limit: int | None = Field(
        default=None, ge=1, description="Offset-based: maximum number of results."
    )
    offset: int | None = Field(
        default=None, ge=0, description="Offset-based: number of results to skip."
    )
