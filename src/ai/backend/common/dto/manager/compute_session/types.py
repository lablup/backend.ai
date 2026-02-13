from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

__all__ = (
    "OrderDirection",
    "ComputeSessionFilter",
    "ComputeSessionOrderField",
    "ComputeSessionOrder",
)


class OrderDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ComputeSessionOrderField(StrEnum):
    CREATED_AT = "created_at"
    ID = "id"


class ComputeSessionFilter(BaseRequestModel):
    """Filter for compute sessions."""

    status: list[str] | None = Field(default=None, description="Filter by session status")
    scaling_group_name: StringFilter | None = Field(
        default=None, description="Filter by scaling group name"
    )


class ComputeSessionOrder(BaseRequestModel):
    """Order specification for compute sessions."""

    field: ComputeSessionOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")
