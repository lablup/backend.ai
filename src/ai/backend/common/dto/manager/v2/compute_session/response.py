"""
Response DTOs for Compute Session v2 API.

Node models with container nesting and Payload models for search/detail responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "ContainerNode",
    "ComputeSessionNode",
    "GetComputeSessionDetailPayload",
    "SearchComputeSessionsPayload",
)


class ContainerNode(BaseResponseModel):
    """Node model representing a container (kernel) within a compute session."""

    id: UUID = Field(description="Container (kernel) ID.")
    agent_id: str | None = Field(
        default=None, description="ID of the agent running this container."
    )
    status: str = Field(description="Current status of the container.")
    resource_usage: dict[str, Any] | None = Field(
        default=None, description="Resource usage statistics for this container."
    )


class ComputeSessionNode(BaseResponseModel):
    """Node model representing a compute session with its containers."""

    id: UUID = Field(description="Compute session ID.")
    name: str | None = Field(
        default=None, description="Human-readable name of the compute session."
    )
    type: str = Field(description="Type of the compute session.")
    status: str = Field(description="Current status of the compute session.")
    image: list[str] | None = Field(
        default=None, description="Container images used by this session."
    )
    scaling_group: str | None = Field(
        default=None,
        description="The resource group (scaling group) this session is assigned to.",
    )
    resource_slots: dict[str, Any] | None = Field(
        default=None, description="Resource slots requested for this session."
    )
    occupied_slots: dict[str, Any] | None = Field(
        default=None, description="Currently occupied resource slots."
    )
    created_at: datetime = Field(description="Timestamp when the session was created.")
    terminated_at: datetime | None = Field(
        default=None, description="Timestamp when the session was terminated. Null if still active."
    )
    starts_at: datetime | None = Field(
        default=None, description="Scheduled start time for the session, if applicable."
    )
    containers: list[ContainerNode] = Field(
        default_factory=list, description="List of containers (kernels) belonging to this session."
    )


class GetComputeSessionDetailPayload(BaseResponseModel):
    """Payload for getting a single compute session detail."""

    session: ComputeSessionNode = Field(description="Compute session detail data.")


class SearchComputeSessionsPayload(BaseResponseModel):
    """Payload for paginated compute session search results."""

    items: list[ComputeSessionNode] = Field(description="List of compute session nodes.")
    pagination: PaginationInfo = Field(description="Pagination metadata.")
