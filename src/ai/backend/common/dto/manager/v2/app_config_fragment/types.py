"""Enum types and filters for app_config_fragment v2 DTOs."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID

__all__ = (
    "AppConfigFragmentOrderField",
    "AppConfigFragmentScope",
    "AppConfigScopeTypeFilter",
)


class AppConfigFragmentScope(BaseRequestModel):
    """The scope a scoped app config fragment search acts at."""

    scope_type: AppConfigScopeType = Field(description="Scope the search acts at (domain | user).")
    scope_id: AppConfigScopeID = Field(
        description="Scope identifier: the domain id (domain scope) or the user id (user scope)."
    )

    @model_validator(mode="after")
    def _reject_public(self) -> Self:
        # public maps to the global RBAC scope, which has no scope element to authorize
        # against. Whether a scoped search should reach public fragments is still open.
        if self.scope_type is AppConfigScopeType.PUBLIC:
            raise ValueError("scope_type 'public' is not supported by a scoped search.")
        return self


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
