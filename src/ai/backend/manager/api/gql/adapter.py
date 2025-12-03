"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from typing import Optional

from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    QueryPagination,
)

DEFAULT_PAGINATION_LIMIT = 10


class BaseGQLAdapter:
    """Base adapter providing common GraphQL query building utilities."""

    def build_pagination(
        self,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        cursor_condition: Optional[QueryCondition] = None,
        default_order: Optional[QueryOrder] = None,
    ) -> QueryPagination:
        """Build pagination from GraphQL pagination arguments.

        For cursor-based pagination (first/after or last/before), cursor_condition
        and default_order are required. These should be provided by the domain adapter
        after decoding the cursor.

        If no pagination parameters are provided, returns a default OffsetPagination
        with limit=DEFAULT_PAGINATION_LIMIT.
        """
        # Validate and build pagination
        # Count how many pagination modes are being used
        pagination_modes = sum([
            first is not None,
            last is not None,
            limit is not None,
        ])

        if pagination_modes > 1:
            raise InvalidGraphQLParameters(
                "Only one pagination mode allowed: (first/after) OR (last/before) OR (limit/offset)"
            )

        # Build appropriate pagination based on parameters
        if first is not None:
            if first <= 0:
                raise InvalidGraphQLParameters(f"first must be positive, got {first}")
            if after is None:
                raise InvalidGraphQLParameters("after cursor is required when using first")
            if cursor_condition is None or default_order is None:
                raise InvalidGraphQLParameters(
                    "cursor_condition and default_order are required for cursor pagination"
                )
            return CursorForwardPagination(
                first=first,
                cursor_condition=cursor_condition,
                default_order=default_order,
            )
        elif last is not None:
            if last <= 0:
                raise InvalidGraphQLParameters(f"last must be positive, got {last}")
            if before is None:
                raise InvalidGraphQLParameters("before cursor is required when using last")
            if cursor_condition is None or default_order is None:
                raise InvalidGraphQLParameters(
                    "cursor_condition and default_order are required for cursor pagination"
                )
            return CursorBackwardPagination(
                last=last,
                cursor_condition=cursor_condition,
                default_order=default_order,
            )
        elif limit is not None:
            if limit <= 0:
                raise InvalidGraphQLParameters(f"limit must be positive, got {limit}")
            if offset is not None and offset < 0:
                raise InvalidGraphQLParameters(f"offset must be non-negative, got {offset}")
            return OffsetPagination(limit=limit, offset=offset or 0)

        # Default pagination when no parameters provided
        return OffsetPagination(limit=DEFAULT_PAGINATION_LIMIT, offset=0)
