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

from .creators import (
    DomainFairShareCreatorSpec,
    ProjectFairShareCreatorSpec,
    UserFairShareCreatorSpec,
)
from .repositories import FairShareRepositories
from .repository import FairShareRepository
from .types import (
    DomainFairShareEntitySearchResult,
    DomainFairShareSearchScope,
    ProjectFairShareEntitySearchResult,
    ProjectFairShareSearchScope,
    UserFairShareEntitySearchResult,
    UserFairShareSearchScope,
)
from .upserters import (
    DomainFairShareBulkWeightUpserterSpec,
    DomainFairShareUpserterSpec,
    ProjectFairShareBulkWeightUpserterSpec,
    ProjectFairShareUpserterSpec,
    UserFairShareBulkWeightUpserterSpec,
    UserFairShareUpserterSpec,
)

__all__ = (
    # Repositories
    "FairShareRepositories",
    "FairShareRepository",
    # Creator specs
    "DomainFairShareCreatorSpec",
    "ProjectFairShareCreatorSpec",
    "UserFairShareCreatorSpec",
    # Upserter specs
    "DomainFairShareUpserterSpec",
    "ProjectFairShareUpserterSpec",
    "UserFairShareUpserterSpec",
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
    # Scope types
    "DomainFairShareSearchScope",
    "ProjectFairShareSearchScope",
    "UserFairShareSearchScope",
    # Entity-based search results
    "DomainFairShareEntitySearchResult",
    "ProjectFairShareEntitySearchResult",
    "UserFairShareEntitySearchResult",
)
