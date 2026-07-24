"""Request DTOs for app_config_fragment v2."""

from __future__ import annotations

from typing import Any, Self

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.dto.manager.v2.app_config_fragment.types import (
    AppConfigFragmentOrderField,
    AppConfigScopeTypeFilter,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID

__all__ = (
    "AdminSearchAppConfigFragmentInput",
    "AppConfigFragmentFilter",
    "AppConfigFragmentOrder",
    "AppConfigFragmentScope",
    "AppConfigFragmentUpdateItem",
    "BulkPurgeAppConfigFragmentInput",
    "BulkUpdateAppConfigFragmentInput",
    "CreateAppConfigFragmentInput",
    "ScopedSearchAppConfigFragmentInput",
    "UpdateAppConfigFragmentInput",
)


class CreateAppConfigFragmentInput(BaseRequestModel):
    """Input for creating a new app config fragment at a given scope."""

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Registered config name.",
    )
    scope_type: AppConfigScopeType = Field(
        description="Scope the fragment is written at (public | domain | user)."
    )
    scope_id: AppConfigScopeID | None = Field(
        default=None,
        description="Scope identifier: the domain id (domain scope) or the user id (user scope). "
        "Null for public scope, which has no owner.",
    )
    config: dict[str, Any] = Field(description="The fragment's JSON config document.")

    @model_validator(mode="after")
    def _check_scope_id(self) -> Self:
        if self.scope_type is AppConfigScopeType.PUBLIC:
            if self.scope_id is not None:
                raise ValueError("scope_id must be null for public scope.")
        elif self.scope_id is None:
            raise ValueError("scope_id is required for domain and user scopes.")
        return self


class UpdateAppConfigFragmentInput(BaseRequestModel):
    """Input for updating one app config fragment's config document.

    The target fragment is identified by the request path, not by this body.
    """

    config: dict[str, Any] = Field(description="The replacement JSON config document.")


class AppConfigFragmentUpdateItem(BaseRequestModel):
    """One item of a bulk update, carrying its own target id.

    Bulk requests address many fragments in a single call, so the id belongs in the body
    here — unlike the single-fragment :class:`UpdateAppConfigFragmentInput`.
    """

    id: AppConfigFragmentID = Field(description="App config fragment id to update.")
    config: dict[str, Any] = Field(description="The replacement JSON config document.")


class BulkUpdateAppConfigFragmentInput(BaseRequestModel):
    """Input for updating many fragments' config documents (per-item partial success)."""

    items: list[AppConfigFragmentUpdateItem] = Field(
        min_length=1, description="Fragments to update, each identified by its id."
    )


class BulkPurgeAppConfigFragmentInput(BaseRequestModel):
    """Input for purging many fragments (per-item partial success)."""

    ids: list[AppConfigFragmentID] = Field(min_length=1, description="Fragment ids to purge.")


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
    AND: list[Self] | None = Field(default=None, description="Match all of the given sub-filters.")
    OR: list[Self] | None = Field(default=None, description="Match any of the given sub-filters.")
    NOT: list[Self] | None = Field(default=None, description="Negate the given sub-filters.")


AppConfigFragmentFilter.model_rebuild()


class AppConfigFragmentOrder(BaseRequestModel):
    """Order specifier for app config fragment search."""

    field: AppConfigFragmentOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchAppConfigFragmentInput(BaseRequestModel):
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
    """The scopes a scoped fragment search runs at, keyed by scope kind.

    Each category list is OR'd internally and across categories. ``public`` is a flag rather
    than a list: it names one global scope that owns no id. Raises if every field is empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domain ids whose fragments to search."
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="User ids whose fragments to search."
    )
    public: bool | None = Field(
        default=None, description="Search the public scope, which has no owner."
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> Self:
        if not self.domain and not self.user and not self.public:
            raise ValueError(
                "AppConfigFragmentScope requires a non-empty value for 'domain', 'user' or 'public'"
            )
        return self


class ScopedSearchAppConfigFragmentInput(BaseRequestModel):
    """Input for a scoped fragment search, keyed by the scope the fragments are written at."""

    scope: AppConfigFragmentScope = Field(description="The scope to search at.")
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
