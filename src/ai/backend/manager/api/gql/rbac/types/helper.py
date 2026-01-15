"""Utility functions for RBAC GraphQL types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 25


@dataclass(frozen=True)
class PaginationResult(Generic[T]):
    """Result of in-memory pagination."""

    items: list[T]
    has_next_page: bool
    has_previous_page: bool
    total_count: int


def paginate_in_memory(
    items: list[T],
    first: Optional[int],
    after: Optional[str],
    last: Optional[int],
    before: Optional[str],
    limit: Optional[int],
    offset: Optional[int],
) -> PaginationResult[T]:
    """Paginate items in memory.

    Args:
        items: The full list of items to paginate.
        first: Cursor-based pagination - return first N items.
        after: Cursor-based pagination - return items after cursor (not implemented).
        last: Cursor-based pagination - return last N items (not implemented).
        before: Cursor-based pagination - return items before cursor (not implemented).
        limit: Offset-based pagination - maximum items to return.
        offset: Offset-based pagination - number of items to skip.

    Returns:
        PaginationResult containing paginated items and pagination metadata.
    """
    total = len(items)

    # Offset-based pagination takes precedence if provided
    if limit is not None or offset is not None:
        start = offset or 0
        end = start + (limit or DEFAULT_PAGE_SIZE)
        paginated = items[start:end]
        has_next = end < total
        has_prev = start > 0
    else:
        # Cursor-based (simplified)
        paginated = items[:first] if first else items
        has_next = bool(first and len(items) > first)
        has_prev = False

    return PaginationResult(
        items=paginated,
        has_next_page=has_next,
        has_previous_page=has_prev,
        total_count=total,
    )
