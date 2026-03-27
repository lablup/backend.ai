"""Common DTOs for admin GraphQL module."""

from __future__ import annotations

from .request import GraphQLRequest
from .response import GraphQLResponse

__all__ = (
    "GraphQLRequest",
    "GraphQLResponse",
)
