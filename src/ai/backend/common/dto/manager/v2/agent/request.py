"""
Request DTOs for Agent v2 API.

Input models for agent search and path parameters.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.agent.types import (
    AgentOrderField,
    AgentStatusFilter,
    OrderDirection,
)

__all__ = (
    "AdminSearchAgentsInput",
    "AgentFilter",
    "AgentOrder",
    "AgentPathParam",
    "SearchAgentsInput",
)


# ---------------------------------------------------------------------------
# Path parameter
# ---------------------------------------------------------------------------


class AgentPathParam(BaseRequestModel):
    """Path parameter for agent-scoped endpoints."""

    agent_id: str


# ---------------------------------------------------------------------------
# Filter / Order
# ---------------------------------------------------------------------------


class AgentFilter(BaseRequestModel):
    """Filter conditions for agent search."""

    status: AgentStatusFilter | None = Field(
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
    """Order specification for agent search."""

    field: AgentOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


# ---------------------------------------------------------------------------
# Search / query
# ---------------------------------------------------------------------------


class SearchAgentsInput(BaseRequestModel):
    """Input for paginated agent search."""

    filter: AgentFilter | None = None
    order: list[AgentOrder] | None = None
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)
    offset: int = Field(default=0, ge=0)


class AdminSearchAgentsInput(BaseRequestModel):
    """Input for admin-scoped paginated agent search with cursor and offset pagination."""

    filter: AgentFilter | None = None
    order: list[AgentOrder] | None = None
    # Cursor pagination
    first: int | None = None
    after: str | None = None
    last: int | None = None
    before: str | None = None
    # Offset pagination
    limit: int | None = None
    offset: int | None = None
