"""Request DTOs for admin GraphQL module."""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("GraphQLRequest",)


class GraphQLRequest(BaseRequestModel):
    """Request body for GraphQL queries."""

    query: str = Field(description="GraphQL query string")
    variables: dict[str, Any] | None = Field(
        default=None,
        description="GraphQL query variables",
    )
    operation_name: str | None = Field(
        default=None,
        description="Name of the GraphQL operation to execute",
        validation_alias=AliasChoices("operation_name", "operationName"),
    )
