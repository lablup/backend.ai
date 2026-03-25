"""
Common types for Compute Session DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "ClusterModeDTO",
    "ComputeSessionFilter",
    "ComputeSessionOrder",
    "ComputeSessionOrderField",
    "OrderDirection",
)


class ClusterModeDTO(StrEnum):
    """Cluster mode enum for DTO layer (matches GQL schema values)."""

    SINGLE_NODE = "SINGLE_NODE"
    MULTI_NODE = "MULTI_NODE"


class ComputeSessionOrderField(StrEnum):
    """Fields available for ordering compute sessions."""

    CREATED_AT = "created_at"
    ID = "id"


class ComputeSessionFilter(BaseRequestModel):
    """Filter for compute sessions."""

    status: list[str] | None = Field(default=None, description="Filter by session status")
    name: StringFilter | None = Field(default=None, description="Filter by session name")
    access_key: StringFilter | None = Field(default=None, description="Filter by access key")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    scaling_group_name: StringFilter | None = Field(
        default=None, description="Filter by scaling group name"
    )


class ComputeSessionOrder(BaseRequestModel):
    """Order specification for compute sessions."""

    field: ComputeSessionOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")
