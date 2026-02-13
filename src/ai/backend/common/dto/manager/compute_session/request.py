from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import ComputeSessionFilter, ComputeSessionOrder

__all__ = ("SearchComputeSessionsRequest",)


class SearchComputeSessionsRequest(BaseRequestModel):
    """Request body for searching compute sessions."""

    filter: ComputeSessionFilter | None = Field(default=None, description="Filter conditions")
    order: list[ComputeSessionOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
