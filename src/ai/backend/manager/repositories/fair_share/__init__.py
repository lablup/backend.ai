"""Fair Share repository package."""

from .creators import (
    DomainFairShareCreatorSpec,
    ProjectFairShareCreatorSpec,
    UserFairShareCreatorSpec,
)
from .options import (
    DomainFairShareConditions,
    DomainFairShareOrders,
    ProjectFairShareConditions,
    ProjectFairShareOrders,
    UserFairShareConditions,
    UserFairShareOrders,
)
from .repositories import FairShareRepositories
from .repository import FairShareRepository
from .types import (
    DomainFairShareSearchScope,
    ProjectFairShareSearchScope,
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
)
