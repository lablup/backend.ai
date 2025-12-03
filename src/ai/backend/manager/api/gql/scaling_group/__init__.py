"""GraphQL scaling group module."""

from .adapter import ScalingGroupGQLAdapter
from .resolver import all_scaling_groups_v2, scaling_groups_v2
from .types import (
    ScalingGroupFilterGQL,
    ScalingGroupOrderByGQL,
    ScalingGroupOrderFieldGQL,
    ScalingGroupV2GQL,
)

__all__ = (
    # Adapters
    "ScalingGroupGQLAdapter",
    # Types
    "ScalingGroupV2GQL",
    "ScalingGroupFilterGQL",
    "ScalingGroupOrderByGQL",
    "ScalingGroupOrderFieldGQL",
    # Resolvers
    "scaling_groups_v2",
    "all_scaling_groups_v2",
)
