"""
Common types for container registry DTO v2.
"""

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.container_registry import ContainerRegistryType

__all__ = (
    "ContainerRegistryOrderField",
    "ContainerRegistryType",
    "ContainerRegistryTypeFilter",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ContainerRegistryOrderField(StrEnum):
    """Fields available for ordering container registries."""

    REGISTRY_NAME = "registry_name"
    URL = "url"
    TYPE = "type"
    IS_GLOBAL = "is_global"


class ContainerRegistryTypeFilter(BaseRequestModel):
    """Filter for container registry type enum fields.

    Supports equals, in, not_equals, and not_in operations.
    """

    equals: ContainerRegistryType | None = Field(
        default=None, description="Exact match for registry type."
    )
    in_: list[ContainerRegistryType] | None = Field(
        default=None, alias="in", description="Match any of the provided types."
    )
    not_equals: ContainerRegistryType | None = Field(
        default=None, description="Exclude exact type match."
    )
    not_in: list[ContainerRegistryType] | None = Field(
        default=None, description="Exclude any of the provided types."
    )
