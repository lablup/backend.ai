"""
Common types for Domain DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "DomainFairShareScopeDTO",
    "DomainOrderField",
    "DomainProjectFilter",
    "DomainScope",
    "DomainUsageScopeDTO",
    "DomainUserFilter",
    "OrderDirection",
)


class DomainOrderField(StrEnum):
    """Fields available for ordering domains."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    IS_ACTIVE = "is_active"
    PROJECT_NAME = "project_name"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


class DomainProjectFilter(BaseRequestModel):
    """Nested filter for projects belonging to a domain."""

    name: StringFilter | None = None
    is_active: bool | None = None


class DomainUserFilter(BaseRequestModel):
    """Nested filter for users belonging to a domain."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None


class DomainFairShareScopeDTO(BaseRequestModel):
    """Scope for domain fair share queries."""

    resource_group_name: str = Field(description="Resource group to filter fair shares by.")


class DomainUsageScopeDTO(BaseRequestModel):
    """Scope for domain usage bucket queries."""

    resource_group_name: str = Field(description="Resource group to filter usage buckets by.")


class DomainScope(BaseRequestModel):
    """Scope for the scoped domain query.

    Each list is OR'd internally. Raises an error if every field is empty.
    """

    resource_group: list[UUIDScope] | None = Field(
        default=None, description="Resource groups whose domains are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> DomainScope:
        if not self.resource_group:
            raise ValueError("DomainScope requires a non-empty value for 'resource_group'")
        return self
