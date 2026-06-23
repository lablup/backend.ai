"""Request DTOs for app_config_allow_list v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.app_config_allow_list.types import (
    AppConfigAllowListOrderField,
    AppConfigScopeType,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "AppConfigAllowListFilter",
    "AppConfigAllowListOrder",
    "CreateAppConfigAllowListInput",
    "PurgeAppConfigAllowListInput",
    "SearchAppConfigAllowListInput",
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


class PurgeAppConfigAllowListInput(BaseRequestModel):
    """Input for purging an app config allow-list entry."""

    id: UUID = Field(description="App config allow-list entry id to purge.")


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
