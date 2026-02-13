"""
Common types for Agent REST API.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AgentOrderField",
    "AgentStatusEnum",
    "AgentStatusEnumFilter",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class AgentStatusEnum(StrEnum):
    """Agent statuses available for filtering."""

    ALIVE = "ALIVE"
    LOST = "LOST"
    RESTARTING = "RESTARTING"
    TERMINATED = "TERMINATED"


class AgentStatusEnumFilter(BaseRequestModel):
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


class AgentOrderField(StrEnum):
    """Fields available for ordering agents."""

    ID = "id"
    STATUS = "status"
    SCALING_GROUP = "scaling_group"
