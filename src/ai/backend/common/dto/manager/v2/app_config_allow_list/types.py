"""Enum types and filters for app_config_allow_list v2 DTOs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AppConfigScopeType",
    "AppConfigScopeTypeFilter",
    "AppConfigAllowListOrderField",
)


class AppConfigScopeType(StrEnum):
    PUBLIC = "public"
    DOMAIN = "domain"
    USER = "user"


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


class AppConfigAllowListOrderField(StrEnum):
    CONFIG_NAME = "config_name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
