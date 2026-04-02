"""
Common types for Group (Project) DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "DomainProjectScopeDTO",
    "OrderDirection",
    "ProjectDomainFilter",
    "ProjectOrderField",
    "ProjectType",
    "ProjectTypeFilter",
    "ProjectUserFilter",
)


class ProjectType(StrEnum):
    """Project type determining its purpose and behavior."""

    GENERAL = "general"
    MODEL_STORE = "model-store"


class ProjectOrderField(StrEnum):
    """Fields available for ordering projects."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    IS_ACTIVE = "is_active"
    TYPE = "type"
    DOMAIN_NAME = "domain_name"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


class ProjectTypeFilter(BaseRequestModel):
    """Filter for project type fields."""

    equals: ProjectType | None = None
    in_: list[ProjectType] | None = None
    not_equals: ProjectType | None = None
    not_in: list[ProjectType] | None = None


class ProjectDomainFilter(BaseRequestModel):
    """Nested filter for the domain a project belongs to."""

    name: StringFilter | None = None
    is_active: bool | None = None


class ProjectUserFilter(BaseRequestModel):
    """Nested filter for users belonging to a project."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None


class DomainProjectScopeDTO(BaseRequestModel):
    """Scope for domain-level project queries."""

    domain_name: str = Field(description="Domain name to scope the query.")
