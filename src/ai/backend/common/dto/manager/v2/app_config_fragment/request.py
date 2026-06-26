"""Request DTOs for app_config_fragment v2."""

from __future__ import annotations

from typing import Any, Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigFragmentOrderField,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "AppConfigFragmentFilter",
    "AppConfigFragmentOrder",
    "AppConfigFragmentScope",
    "CreateAppConfigFragmentInput",
    "PurgeAppConfigFragmentInput",
    "ScopedSearchAppConfigFragmentInput",
    "SearchAppConfigFragmentInput",
    "UpdateAppConfigFragmentInput",
)


class CreateAppConfigFragmentInput(BaseRequestModel):
    """Input for creating a new app config fragment at a given scope (superadmin only)."""

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Registered config name (FK to app_config_definitions).",
    )
    scope_type: AppConfigScopeType = Field(
        description="Scope the fragment is written at (public | domain | user)."
    )
    scope_id: str = Field(
        description="Scope identifier: 'public' for public, the domain name, or the user id.",
    )
    config: dict[str, Any] = Field(description="The fragment's JSON config document.")


class UpdateAppConfigFragmentInput(BaseRequestModel):
    """Input for updating an app config fragment's config document."""

    config: dict[str, Any] = Field(description="The replacement JSON config document.")


class PurgeAppConfigFragmentInput(BaseRequestModel):
    """Input for purging an app config fragment."""

    id: UUID = Field(description="App config fragment id to purge.")


class AppConfigFragmentFilter(BaseRequestModel):
    """Filter for app config fragment search."""

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


class AppConfigFragmentOrder(BaseRequestModel):
    """Order specifier for app config fragment search."""

    field: AppConfigFragmentOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchAppConfigFragmentInput(BaseRequestModel):
    """Input for paginated app config fragment search (superadmin only)."""

    filter: AppConfigFragmentFilter | None = Field(default=None, description="Filter conditions.")
    order: list[AppConfigFragmentOrder] | None = Field(
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


class AppConfigFragmentScope(BaseRequestModel):
    """Scope for a scoped fragment search — OR across all domain/user items.

    Raises if every category is empty.
    """

    domain: list[UUID] | None = Field(
        default=None, description="Domain ids whose fragments to search."
    )
    user: list[UUID] | None = Field(default=None, description="User ids whose fragments to search.")

    @model_validator(mode="after")
    def _require_non_empty(self) -> Self:
        if not self.domain and not self.user:
            raise ValueError(
                "AppConfigFragmentScope requires a non-empty value for 'domain' or 'user'"
            )
        return self


class ScopedSearchAppConfigFragmentInput(BaseRequestModel):
    """Input for a scoped fragment search keyed by domain/user scope (OR-combined)."""

    scope: AppConfigFragmentScope = Field(description="Scope (OR across all items).")
    order: list[AppConfigFragmentOrder] | None = Field(
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
