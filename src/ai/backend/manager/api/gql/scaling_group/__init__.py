"""GraphQL scaling group module."""

from .adapter import ScalingGroupGQLAdapter
from .resolver import scaling_groups_v2
from .types import (
    GQLScalingGroupFilter,
    GQLScalingGroupOrderBy,
    GQLScalingGroupOrderField,
    GQLScalingGroupV2,
)

__all__ = (
    # Adapters
    "ScalingGroupGQLAdapter",
    # Types
    "GQLScalingGroupV2",
    "GQLScalingGroupFilter",
    "GQLScalingGroupOrderBy",
    "GQLScalingGroupOrderField",
    # Resolvers
    "scaling_groups_v2",
)
