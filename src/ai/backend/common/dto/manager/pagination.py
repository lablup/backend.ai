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
    limit: int = Field(description="Maximum items returned", ge=1)
