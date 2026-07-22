"""Enum types and filters for app_config_fragment v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID

__all__ = (
    "AppConfigFragmentOrderField",
    "AppConfigFragmentScope",
    "AppConfigFragmentSearchScopeType",
    "AppConfigScopeTypeFilter",
)


class AppConfigFragmentSearchScopeType(StrEnum):
    """The scope a scoped fragment search may act at.

    A subset of :class:`AppConfigScopeType`: a scoped search is authorized against one
    owned RBAC scope, and ``public`` maps to the global scope, which has no scope element
    to check. Whether public fragments should be reachable from a scoped search is still
    open — until it is decided, the type says they are not.
    """

    DOMAIN = "domain"
    USER = "user"


class AppConfigFragmentScope(BaseRequestModel):
    """The scope a scoped app config fragment search acts at."""

    scope_type: AppConfigFragmentSearchScopeType = Field(
        description="Scope the search acts at (domain | user)."
    )
    scope_id: AppConfigScopeID = Field(
        description="Scope identifier: the domain id (domain scope) or the user id (user scope)."
    )


class AppConfigScopeTypeFilter(BaseRequestModel):
    """Filter for the scope_type enum field."""

    equals: AppConfigScopeType | None = Field(default=None, description="Exact scope type match.")
    in_: list[AppConfigScopeType] | None = Field(
        default=None, alias="in", description="Match any of the provided scope types."
    )
    not_equals: AppConfigScopeType | None = Field(
        default=None, description="Exclude exact scope type match."
    )
    not_in: list[AppConfigScopeType] | None = Field(
        default=None, description="Exclude any of the provided scope types."
    )


class AppConfigFragmentOrderField(StrEnum):
    CONFIG_NAME = "config_name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
