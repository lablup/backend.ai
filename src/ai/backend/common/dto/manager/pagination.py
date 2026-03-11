"""
Shared pagination DTOs for manager API responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ("PaginationInfo",)


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")
