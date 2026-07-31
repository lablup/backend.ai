"""
Common types for Domain DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.identifier.resource_group import ResourceGroupID

__all__ = (
    "DomainFairShareScopeDTO",
    "DomainOrderField",
    "DomainProjectFilter",
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

    resource_group_name: str | None = Field(
        default=None,
        description="Resource group name. Deprecated; use resource_group_id.",
        json_schema_extra={"deprecated": True},
    )
    resource_group_id: ResourceGroupID | None = Field(
        default=None, description="Resource group ID."
    )


class DomainUsageScopeDTO(BaseRequestModel):
    """Scope for domain usage bucket queries."""

    resource_group_name: str = Field(description="Resource group to filter usage buckets by.")
