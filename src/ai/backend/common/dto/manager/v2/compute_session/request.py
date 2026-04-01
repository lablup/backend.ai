"""
Request DTOs for Compute Session v2 API.

Input models for compute session search and path parameters.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.compute_session.types import (
    ComputeSessionFilter,
    ComputeSessionOrder,
)

__all__ = (
    "ComputeSessionPathParam",
    "SearchComputeSessionsInput",
)


# ---------------------------------------------------------------------------
# Path parameter
# ---------------------------------------------------------------------------


class ComputeSessionPathParam(BaseRequestModel):
    """Path parameter for compute session-scoped endpoints."""

    session_id: str


# ---------------------------------------------------------------------------
# Search / query
# ---------------------------------------------------------------------------


class SearchComputeSessionsInput(BaseRequestModel):
    """Input for paginated compute session search."""

    filter: ComputeSessionFilter | None = None
    order: list[ComputeSessionOrder] | None = None
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)
    offset: int = Field(default=0, ge=0)
