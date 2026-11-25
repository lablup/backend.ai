"""
Common types for container registry DTO v2.
"""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION

__all__ = (
    "ContainerRegistryOrderField",
    "ContainerRegistryScope",
    "ContainerRegistryType",
    "ContainerRegistryTypeFilter",
    "OrderDirection",
)


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


class ContainerRegistryScope(BaseRequestModel):
    """Scope for the scoped container registry query. Every item of every list is OR'd."""

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose related container registries are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None,
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Projects whose related container registries are being read"
        ),
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> Self:
        if not self.domain and not self.project:
            raise ValueError(
                "ContainerRegistryScope requires a non-empty value for 'domain' or 'project'"
            )
        return self
