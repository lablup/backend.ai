"""Fair Share repository package."""

from ai.backend.manager.models.fair_share.conditions import (
    DomainFairShareConditions,
    ProjectFairShareConditions,
    UserFairShareConditions,
)
from ai.backend.manager.models.fair_share.orders import (
    DomainFairShareOrders,
    ProjectFairShareOrders,
    UserFairShareOrders,
)

from .repositories import FairShareRepositories
from .repository import FairShareRepository
from .types import (
    DomainFairShareEntitySearchResult,
    ProjectFairShareEntitySearchResult,
    UserFairShareEntitySearchResult,
)
from .upserters import (
    DomainFairShareBulkWeightUpserterSpec,
    ProjectFairShareBulkWeightUpserterSpec,
    UserFairShareBulkWeightUpserterSpec,
)

__all__ = (
    # Repositories
    "FairShareRepositories",
    "FairShareRepository",
    # Bulk weight upserter specs
    "DomainFairShareBulkWeightUpserterSpec",
    "ProjectFairShareBulkWeightUpserterSpec",
    "UserFairShareBulkWeightUpserterSpec",
    # Query conditions
    "DomainFairShareConditions",
    "ProjectFairShareConditions",
    "UserFairShareConditions",
    # Query orders
    "DomainFairShareOrders",
    "ProjectFairShareOrders",
    "UserFairShareOrders",
    # Entity-based search results
    "DomainFairShareEntitySearchResult",
    "ProjectFairShareEntitySearchResult",
    "UserFairShareEntitySearchResult",
)
