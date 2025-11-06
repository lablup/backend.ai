"""Base GraphQL adapter providing common utilities."""

from __future__ import annotations

from typing import Optional

from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    QueryPagination,
)


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
    ) -> Optional[QueryPagination]:
        """Build pagination from GraphQL pagination arguments."""
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
            return CursorForwardPagination(first=first, after=after)
        elif last is not None:
            if last <= 0:
                raise InvalidGraphQLParameters(f"last must be positive, got {last}")
            if before is None:
                raise InvalidGraphQLParameters("before cursor is required when using last")
            return CursorBackwardPagination(last=last, before=before)
        elif limit is not None:
            if limit <= 0:
                raise InvalidGraphQLParameters(f"limit must be positive, got {limit}")
            if offset is not None and offset < 0:
                raise InvalidGraphQLParameters(f"offset must be non-negative, got {offset}")
            return OffsetPagination(limit=limit, offset=offset or 0)

        return None
