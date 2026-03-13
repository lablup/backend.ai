"""
Shared pagination DTOs for manager API responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ("PaginationInfo",)


class PaginationInfo(BaseModel):
    """Pagination information for list responses."""

    total: int = Field(description="Total number of items", ge=0)
    offset: int = Field(description="Number of items skipped", ge=0)
    limit: int | None = Field(
        default=None,
        description="Maximum items returned; optional to accommodate cursor-based pagination where an explicit limit may not apply",
        ge=1,  # ge constraint only applies when the value is not None
    )
