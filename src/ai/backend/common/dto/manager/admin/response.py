"""Response DTOs for admin GraphQL module."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("GraphQLResponse",)


class GraphQLResponse(BaseResponseModel):
    """Response for GraphQL queries.

    The shape follows the standard GraphQL response specification.
    """

    data: dict[str, Any] | None = Field(
        default=None,
        description="GraphQL query result data",
    )
    errors: list[dict[str, Any]] | None = Field(
        default=None,
        description="GraphQL execution errors",
    )
