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
from .repository import FairShareRepository
from .upserters import (
    DomainFairShareUpserterSpec,
    ProjectFairShareUpserterSpec,
    UserFairShareUpserterSpec,
)

__all__ = (
    # Repository
    "FairShareRepository",
    # Creator specs
    "DomainFairShareCreatorSpec",
    "ProjectFairShareCreatorSpec",
    "UserFairShareCreatorSpec",
    # Upserter specs
    "DomainFairShareUpserterSpec",
    "ProjectFairShareUpserterSpec",
    "UserFairShareUpserterSpec",
    # Query conditions
    "DomainFairShareConditions",
    "ProjectFairShareConditions",
    "UserFairShareConditions",
    # Query orders
    "DomainFairShareOrders",
    "ProjectFairShareOrders",
    "UserFairShareOrders",
)
