"""Fair Share GQL types package."""

from .common import (
    FairShareCalculationSnapshotGQL,
    FairShareSpecGQL,
    ResourceSlotEntryGQL,
    ResourceSlotGQL,
    ResourceWeightEntryInputGQL,
)
from .domain import (
    DomainFairShareConnection,
    DomainFairShareEdge,
    DomainFairShareFilter,
    DomainFairShareGQL,
    DomainFairShareOrderBy,
    DomainFairShareOrderField,
    UpsertDomainFairShareWeightInput,
    UpsertDomainFairShareWeightPayload,
)
from .project import (
    ProjectFairShareConnection,
    ProjectFairShareEdge,
    ProjectFairShareFilter,
    ProjectFairShareGQL,
    ProjectFairShareOrderBy,
    ProjectFairShareOrderField,
    UpsertProjectFairShareWeightInput,
    UpsertProjectFairShareWeightPayload,
)
from .user import (
    UpsertUserFairShareWeightInput,
    UpsertUserFairShareWeightPayload,
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
    "ResourceWeightEntryInputGQL",
    "FairShareSpecGQL",
    "FairShareCalculationSnapshotGQL",
    # Domain
    "DomainFairShareGQL",
    "DomainFairShareConnection",
    "DomainFairShareEdge",
    "DomainFairShareFilter",
    "DomainFairShareOrderField",
    "DomainFairShareOrderBy",
    "UpsertDomainFairShareWeightInput",
    "UpsertDomainFairShareWeightPayload",
    # Project
    "ProjectFairShareGQL",
    "ProjectFairShareConnection",
    "ProjectFairShareEdge",
    "ProjectFairShareFilter",
    "ProjectFairShareOrderField",
    "ProjectFairShareOrderBy",
    "UpsertProjectFairShareWeightInput",
    "UpsertProjectFairShareWeightPayload",
    # User
    "UserFairShareGQL",
    "UserFairShareConnection",
    "UserFairShareEdge",
    "UserFairShareFilter",
    "UserFairShareOrderField",
    "UserFairShareOrderBy",
    "UpsertUserFairShareWeightInput",
    "UpsertUserFairShareWeightPayload",
]
