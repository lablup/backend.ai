"""GraphQL resource group module."""

from .resolver import (
    admin_allowed_domains_for_resource_group_v2,
    admin_allowed_projects_for_resource_group_v2,
    admin_allowed_resource_groups_for_domain_v2,
    admin_allowed_resource_groups_for_project_v2,
    admin_create_resource_group_v2,
    admin_delete_resource_group_v2,
    admin_resource_group_v2,
    admin_resource_groups,
    admin_update_allowed_domains_for_resource_group_v2,
    admin_update_allowed_projects_for_resource_group_v2,
    admin_update_allowed_resource_groups_for_domain_v2,
    admin_update_allowed_resource_groups_for_project_v2,
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
    "admin_resource_group_v2",
    "admin_resource_groups",
    "admin_allowed_resource_groups_for_domain_v2",
    "admin_allowed_resource_groups_for_project_v2",
    "admin_allowed_domains_for_resource_group_v2",
    "admin_allowed_projects_for_resource_group_v2",
    # Query Resolvers - Legacy (deprecated)
    "resource_groups",
    # Mutation Resolvers - Admin
    "admin_create_resource_group_v2",
    "admin_delete_resource_group_v2",
    "admin_update_resource_group_fair_share_spec",
    "admin_update_resource_group",
    "admin_update_allowed_resource_groups_for_domain_v2",
    "admin_update_allowed_resource_groups_for_project_v2",
    "admin_update_allowed_domains_for_resource_group_v2",
    "admin_update_allowed_projects_for_resource_group_v2",
    # Mutation Resolvers - Legacy (deprecated)
    "update_resource_group_fair_share_spec",
)
