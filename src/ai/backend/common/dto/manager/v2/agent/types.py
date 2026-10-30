"""
Common types for Agent DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "AgentOrderField",
    "AgentUsage",
    "AgentUsedBy",
    "AgentStatusEnum",
    "AgentStatusFilter",
    "ConflictingSessionCleanupPolicyEnum",
    "OrderDirection",
)


class AgentStatusEnum(StrEnum):
    """Agent statuses available for filtering."""

    ALIVE = "ALIVE"
    LOST = "LOST"
    RESTARTING = "RESTARTING"
    TERMINATED = "TERMINATED"


class ConflictingSessionCleanupPolicyEnum(StrEnum):
    """How to clean up sessions that conflict with an agent's resource group change."""

    TERMINATE = "terminate"
    # Re-enqueue conflicting sessions back to PENDING. Not implemented yet.
    RESCHEDULE = "reschedule"


class AgentOrderField(StrEnum):
    """Fields available for ordering agents."""

    ID = "id"
    STATUS = "status"
    SCALING_GROUP = "scaling_group"
    FIRST_CONTACT = "first_contact"
    SCHEDULABLE = "schedulable"


class AgentStatusFilter(BaseRequestModel):
    """Filter for agent status enum fields.

    Supports equals, in, not_equals, and not_in operations,
    following the Strawberry GQL EnumFilter pattern.
    """

    equals: AgentStatusEnum | None = Field(
        default=None, description="Exact match for agent status."
    )
    in_: list[AgentStatusEnum] | None = Field(
        default=None, alias="in", description="Match any of the provided statuses."
    )
    not_equals: AgentStatusEnum | None = Field(
        default=None, description="Exclude exact status match."
    )
    not_in: list[AgentStatusEnum] | None = Field(
        default=None, description="Exclude any of the provided statuses."
    )


class AgentUsedBy(BaseRequestModel):
    """Entities whose use of the agent narrows the result."""

    session: list[UUID] | None = Field(
        default=None, description="Sessions running a kernel on the agent"
    )


class AgentUsage(BaseRequestModel):
    """Uses narrowing the agents read; every id is AND-ed.

    An entity the caller cannot read refuses the request. Agents the caller cannot read
    are left out even when a listed entity is tied to them.
    """

    used_by: AgentUsedBy | None = Field(
        default=None, description="Entities whose use of the agent narrows the result"
    )
