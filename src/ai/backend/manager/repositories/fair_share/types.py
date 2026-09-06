"""Types for fair share repository operations."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)

__all__ = (
    "DomainFairShareEntitySearchResult",
    "ProjectFairShareEntitySearchResult",
    "UserFairShareEntitySearchResult",
)


# ==================== Entity-based Search Results ====================


@dataclass(frozen=True)
class DomainFairShareEntitySearchResult:
    """Search result for entity-based domain fair share query.

    Contains domains associated with a resource group,
    regardless of whether they have fair share records.
    """

    items: list[DomainFairShareData]
    """List of domain fair share data."""

    total_count: int
    """Total number of items matching the query (before pagination)."""

    has_next_page: bool
    """Whether there are more items after the current page."""

    has_previous_page: bool
    """Whether there are items before the current page."""


@dataclass(frozen=True)
class ProjectFairShareEntitySearchResult:
    """Search result for entity-based project fair share query.

    Contains projects associated with a resource group,
    regardless of whether they have fair share records.
    """

    items: list[ProjectFairShareData]
    """List of project fair share data."""

    total_count: int
    """Total number of items matching the query (before pagination)."""

    has_next_page: bool
    """Whether there are more items after the current page."""

    has_previous_page: bool
    """Whether there are items before the current page."""


@dataclass(frozen=True)
class UserFairShareEntitySearchResult:
    """Search result for entity-based user fair share query.

    Contains users associated with a resource group,
    regardless of whether they have fair share records.
    """

    items: list[UserFairShareData]
    """List of user fair share data."""

    total_count: int
    """Total number of items matching the query (before pagination)."""

    has_next_page: bool
    """Whether there are more items after the current page."""

    has_previous_page: bool
    """Whether there are items before the current page."""
