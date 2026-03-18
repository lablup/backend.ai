from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "PaginationInfo",
    "ContainerDTO",
    "ComputeSessionDTO",
    "GetComputeSessionDetailResponse",
    "SearchComputeSessionsResponse",
)


class ContainerDTO(BaseResponseModel):
    """Container (kernel) DTO."""

    id: UUID
    agent_id: str | None = None
    status: str
    resource_usage: dict[str, Any] | None = None


class ComputeSessionDTO(BaseResponseModel):
    """Compute session DTO."""

    id: UUID
    name: str | None = None
    type: str
    status: str
    image: list[str] | None = None
    scaling_group: str | None = None
    resource_slots: dict[str, Any] | None = None
    occupied_slots: dict[str, Any] | None = None
    created_at: datetime
    terminated_at: datetime | None = None
    starts_at: datetime | None = None
    containers: list[ContainerDTO] = Field(default_factory=list)


class GetComputeSessionDetailResponse(BaseResponseModel):
    """Response for getting a single compute session detail."""

    session: ComputeSessionDTO = Field(description="Compute session detail data")


class SearchComputeSessionsResponse(BaseResponseModel):
    """Response for searching compute sessions."""

    items: list[ComputeSessionDTO] = Field(description="List of compute sessions")
    pagination: PaginationInfo = Field(description="Pagination information")
