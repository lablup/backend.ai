"""Fair Share repository package."""

from .repositories import FairShareRepositories
from .repository import FairShareRepository
from .types import (
    DomainFairShareEntitySearchResult,
    ProjectFairShareEntitySearchResult,
    UserFairShareEntitySearchResult,
)

__all__ = (
    # Repositories
    "FairShareRepositories",
    "FairShareRepository",
    # Entity-based search results
    "DomainFairShareEntitySearchResult",
    "ProjectFairShareEntitySearchResult",
    "UserFairShareEntitySearchResult",
)
