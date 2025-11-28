"""GraphQL scaling group module."""

from .adapter import ScalingGroupGQLAdapter
from .resolver import scaling_groups
from .types import (
    ScalingGroupFilter,
    ScalingGroupOrderBy,
    ScalingGroupOrderField,
    ScalingGroupV2,
)

__all__ = (
    # Adapters
    "ScalingGroupGQLAdapter",
    # Types
    "ScalingGroupV2",
    "ScalingGroupFilter",
    "ScalingGroupOrderBy",
    "ScalingGroupOrderField",
    # Resolvers
    "scaling_groups",
)
