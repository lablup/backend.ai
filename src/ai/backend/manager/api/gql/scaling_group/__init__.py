"""GraphQL scaling group module."""

from .adapter import ScalingGroupGQLAdapter
from .resolver import scaling_groups
from .types import (
    ScalingGroup,
    ScalingGroupFilter,
    ScalingGroupOrderBy,
    ScalingGroupOrderField,
)

__all__ = (
    # Adapters
    "ScalingGroupGQLAdapter",
    # Types
    "ScalingGroup",
    "ScalingGroupFilter",
    "ScalingGroupOrderBy",
    "ScalingGroupOrderField",
    # Resolvers
    "scaling_groups",
)
