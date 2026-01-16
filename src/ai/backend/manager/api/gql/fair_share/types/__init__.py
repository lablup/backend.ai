"""Fair Share GQL types package."""

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
    ResourceSlotEntryGQL,
    ResourceSlotGQL,
)
from .domain import (
    DomainFairShareConnection,
    DomainFairShareEdge,
    DomainFairShareFilter,
    DomainFairShareGQL,
    DomainFairShareOrderBy,
    DomainFairShareOrderField,
)
from .project import (
    ProjectFairShareConnection,
    ProjectFairShareEdge,
    ProjectFairShareFilter,
    ProjectFairShareGQL,
    ProjectFairShareOrderBy,
    ProjectFairShareOrderField,
)
from .user import (
    UserFairShareConnection,
    UserFairShareEdge,
    UserFairShareFilter,
    UserFairShareGQL,
    UserFairShareOrderBy,
    UserFairShareOrderField,
)

__all__ = [
    # Common
    "ResourceSlotEntryGQL",
    "ResourceSlotGQL",
    "FairShareSpecGQL",
    "FairShareCalculationSnapshotGQL",
    # Domain
    "DomainFairShareGQL",
    "DomainFairShareConnection",
    "DomainFairShareEdge",
    "DomainFairShareFilter",
    "DomainFairShareOrderField",
    "DomainFairShareOrderBy",
    # Project
    "ProjectFairShareGQL",
    "ProjectFairShareConnection",
    "ProjectFairShareEdge",
    "ProjectFairShareFilter",
    "ProjectFairShareOrderField",
    "ProjectFairShareOrderBy",
    # User
    "UserFairShareGQL",
    "UserFairShareConnection",
    "UserFairShareEdge",
    "UserFairShareFilter",
    "UserFairShareOrderField",
    "UserFairShareOrderBy",
]
