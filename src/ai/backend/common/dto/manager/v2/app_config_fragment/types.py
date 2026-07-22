"""Enum types and filters for app_config_fragment v2 DTOs."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.app_config.types import AppConfigScopeType

__all__ = (
    "AppConfigFragmentDomainScope",
    "AppConfigFragmentOrderField",
    "AppConfigFragmentUserScope",
    "AppConfigScopeTypeFilter",
)


class AppConfigFragmentDomainScope(BaseRequestModel):
    """Scope for a domain-scoped app config fragment search."""

    domain_id: UUID = Field(description="Domain whose fragments to search.")


class AppConfigFragmentUserScope(BaseRequestModel):
    """Scope for a user-scoped app config fragment search."""

    user_id: UUID = Field(description="User whose fragments to search.")


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
