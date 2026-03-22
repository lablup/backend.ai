"""
Request DTOs for Resource Slot Type REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter

__all__ = (
    "OrderDirection",
    "ResourceSlotTypeOrderField",
    "ResourceSlotTypeFilter",
    "ResourceSlotTypeOrder",
    "ResourceSlotTypePathParam",
    "SearchResourceSlotTypesRequest",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ResourceSlotTypeOrderField(StrEnum):
    """Fields available for ordering resource slot types."""

    SLOT_NAME = "slot_name"
    RANK = "rank"
    DISPLAY_NAME = "display_name"


class ResourceSlotTypeFilter(BaseRequestModel):
    """Filter conditions for resource slot types."""

    slot_name: StringFilter | None = Field(
        default=None,
        description=(
            "Filter by slot name. "
            "Supports equals, contains, starts_with, ends_with, "
            "and their case-insensitive and negated variants."
        ),
    )
    slot_type: StringFilter | None = Field(
        default=None,
        description="Filter by slot type.",
    )
    display_name: StringFilter | None = Field(
        default=None,
        description="Filter by display name.",
    )


class ResourceSlotTypeOrder(BaseRequestModel):
    """Order specification for resource slot types."""

    field: ResourceSlotTypeOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class ResourceSlotTypePathParam(BaseRequestModel):
    """Path parameter for resource slot type slot_name."""

    slot_name: str = Field(description="Resource slot type name")


class SearchResourceSlotTypesRequest(BaseRequestModel):
    """Request body for searching resource slot types with filters, orders, and pagination."""

    filter: ResourceSlotTypeFilter | None = Field(default=None, description="Filter conditions")
    order: list[ResourceSlotTypeOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
