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
    ConflictingSessionCleanupPolicyEnum,
    OrderDirection,
)
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId

__all__ = (
    "AdminSearchAgentsInput",
    "AgentFilter",
    "AgentOrder",
    "AgentPathParam",
    "SearchAgentsInput",
    "UpdateAgentResourceGroupBody",
    "UpdateAgentResourceGroupInput",
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

    id: StringFilter | None = Field(
        default=None,
        description="Filter by agent ID. Supports string match operations.",
    )
    status: AgentStatusFilter | None = Field(
        default=None,
        description="Filter by agent status. Supports equals, in, not_equals, and not_in operations.",
    )
    schedulable: bool | None = Field(
        default=None,
        description="Filter by schedulable flag.",
    )
    scaling_group: StringFilter | None = Field(
        default=None,
        description=(
            "Filter by scaling group name. "
            "Supports equals, contains, starts_with, ends_with, "
            "and their case-insensitive and negated variants."
        ),
    )
    AND: list[AgentFilter] | None = Field(
        default=None, description="All sub-conditions must match."
    )
    OR: list[AgentFilter] | None = Field(
        default=None, description="At least one sub-condition must match."
    )
    NOT: list[AgentFilter] | None = Field(
        default=None, description="None of the sub-conditions must match."
    )


AgentFilter.model_rebuild()


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


class UpdateAgentResourceGroupBody(BaseRequestModel):
    """Mutable part of an agent resource-group change.

    Used directly as the REST request body, where the agent ID is supplied as a
    URL path segment instead of a body field. ``UpdateAgentResourceGroupInput``
    extends this with the agent ID for the GQL/adapter call path.
    """

    resource_group_id: ResourceGroupID = Field(
        description="UUID of the target resource group to move the agent into.",
    )
    policy: ConflictingSessionCleanupPolicyEnum | None = Field(
        default=None,
        description=(
            "How to handle sessions still running on the agent under the old "
            "resource group. Defaults to 'terminate', which is currently the "
            "only supported policy."
        ),
    )
    force: bool = Field(
        default=False,
        description=(
            "When false, the change is rejected with a conflict error if the agent "
            "still has active sessions. When true, the group is changed anyway and "
            "the conflicting sessions are cleaned up per the policy."
        ),
    )


class UpdateAgentResourceGroupInput(UpdateAgentResourceGroupBody):
    """Input for changing the resource group of an agent, carrying the agent ID.

    Extends ``UpdateAgentResourceGroupBody`` with ``agent_id`` for the GQL
    mutation and adapter call path.
    """

    agent_id: AgentId = Field(description="ID of the agent to move.")


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
