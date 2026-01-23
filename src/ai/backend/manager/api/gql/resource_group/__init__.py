"""GraphQL resource group module."""

from .resolver import resource_groups, update_resource_group_fair_share_spec
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
    # Mutation Resolvers
    "update_resource_group_fair_share_spec",
)
