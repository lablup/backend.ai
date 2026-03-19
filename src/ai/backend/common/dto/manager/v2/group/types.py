"""
Common types for Group (Project) DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

__all__ = (
    "DomainProjectScopeDTO",
    "GroupDomainFilter",
    "GroupOrderField",
    "GroupUserFilter",
    "OrderDirection",
    "ProjectType",
    "ProjectTypeFilter",
)


class ProjectType(StrEnum):
    """Project type determining its purpose and behavior."""

    GENERAL = "general"
    MODEL_STORE = "model-store"


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class GroupOrderField(StrEnum):
    """Fields available for ordering groups."""

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


class GroupDomainFilter(BaseRequestModel):
    """Nested filter for the domain a project belongs to."""

    name: StringFilter | None = None
    is_active: bool | None = None


class GroupUserFilter(BaseRequestModel):
    """Nested filter for users belonging to a project."""

    username: StringFilter | None = None
    email: StringFilter | None = None
    is_active: bool | None = None


class DomainProjectScopeDTO(BaseRequestModel):
    """Scope for domain-level project queries."""

    domain_name: str = Field(description="Domain name to scope the query.")
