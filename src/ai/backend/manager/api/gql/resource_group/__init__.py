"""GraphQL resource group module."""

from .resolver import (
    resource_group_resources,
    resource_groups,
    update_resource_group_fair_share_spec,
)
from .types import (
    FairShareScalingGroupSpecGQL,
    ResourceGroupFilterGQL,
    ResourceGroupGQL,
    ResourceGroupOrderByGQL,
    ResourceGroupOrderFieldGQL,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupFairShareSpecPayload,
)

__all__ = (
    # Types
    "FairShareScalingGroupSpecGQL",
    "ResourceGroupGQL",
    "ResourceGroupFilterGQL",
    "ResourceGroupOrderByGQL",
    "ResourceGroupOrderFieldGQL",
    "UpdateResourceGroupFairShareSpecInput",
    "UpdateResourceGroupFairShareSpecPayload",
    # Query Resolvers
    "resource_groups",
    "resource_group_resources",
    # Mutation Resolvers
    "update_resource_group_fair_share_spec",
)
