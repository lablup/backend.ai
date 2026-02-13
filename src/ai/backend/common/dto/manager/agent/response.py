"""
Response DTOs for Agent REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AgentDTO",
    "PaginationInfo",
    "SearchAgentsResponse",
)


class AgentDTO(BaseModel):
    """DTO for agent data."""

    id: str = Field(description="Agent ID")
    status: str = Field(description="Current agent status")
    region: str = Field(description="Region identifier")
    scaling_group: str = Field(description="Assigned scaling group")
    schedulable: bool = Field(description="Whether the agent accepts new sessions")
    available_slots: dict[str, str] = Field(description="Free resource slots")
    occupied_slots: dict[str, str] = Field(description="In-use resource slots")
    addr: str = Field(description="Agent address")
    architecture: str = Field(description="CPU architecture")
    version: str = Field(description="Agent version string")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class SearchAgentsResponse(BaseResponseModel):
    """Response for searching agents."""

    items: list[AgentDTO] = Field(description="List of agents")
    pagination: PaginationInfo = Field(description="Pagination information")
