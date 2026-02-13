"""
Request DTOs for Agent REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter

from .types import AgentOrderField, AgentStatusEnumFilter, OrderDirection

__all__ = (
    "AgentFilter",
    "AgentOrder",
    "SearchAgentsRequest",
)


class AgentFilter(BaseRequestModel):
    """Filter for agents."""

    status: AgentStatusEnumFilter | None = Field(
        default=None,
        description="Filter by agent status. Supports equals, in, not_equals, and not_in operations.",
    )
    resource_group: StringFilter | None = Field(
        default=None,
        description=(
            "Filter by resource group name. "
            "Supports equals, contains, starts_with, ends_with, "
            "and their case-insensitive and negated variants."
        ),
    )


class AgentOrder(BaseRequestModel):
    """Order specification for agents."""

    field: AgentOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchAgentsRequest(BaseRequestModel):
    """Request body for searching agents with filters, orders, and pagination."""

    filter: AgentFilter | None = Field(default=None, description="Filter conditions")
    order: list[AgentOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
