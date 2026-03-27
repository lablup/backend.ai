"""GraphQL resource group module."""

from .resolver import (
    admin_resource_groups,
    admin_update_resource_group,
    admin_update_resource_group_fair_share_spec,
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
    UpdateResourceGroupInput,
    UpdateResourceGroupPayload,
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
    "UpdateResourceGroupInput",
    "UpdateResourceGroupPayload",
    # Query Resolvers - Admin
    "admin_resource_groups",
    # Query Resolvers - Legacy (deprecated)
    "resource_groups",
    # Mutation Resolvers - Admin
    "admin_update_resource_group_fair_share_spec",
    "admin_update_resource_group",
    # Mutation Resolvers - Legacy (deprecated)
    "update_resource_group_fair_share_spec",
)
