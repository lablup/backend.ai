"""GraphQL resource group module."""

from .resolver import all_resource_groups, resource_groups
from .types import (
    ResourceGroupFilterGQL,
    ResourceGroupGQL,
    ResourceGroupOrderByGQL,
    ResourceGroupOrderFieldGQL,
)

__all__ = (
    # Types
    "ResourceGroupGQL",
    "ResourceGroupFilterGQL",
    "ResourceGroupOrderByGQL",
    "ResourceGroupOrderFieldGQL",
    # Resolvers
    "resource_groups",
    "all_resource_groups",
)
