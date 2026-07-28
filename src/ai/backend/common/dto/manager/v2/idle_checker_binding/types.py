from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class IdleCheckerScopeTypeDTO(StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    RESOURCE_GROUP = "resource_group"


class ScopeTypeFilter(BaseRequestModel):
    equals: IdleCheckerScopeTypeDTO | None = Field(default=None)
    in_: list[IdleCheckerScopeTypeDTO] | None = Field(default=None, alias="in")


class IdleCheckerBindingOrderField(StrEnum):
    SCOPE_TYPE = "scope_type"
    ENABLED = "enabled"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
