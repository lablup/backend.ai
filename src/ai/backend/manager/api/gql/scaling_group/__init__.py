"""GraphQL scaling group module."""

from .resolver import all_scaling_groups_v2, scaling_groups_v2
from .types import (
    ScalingGroupFilterGQL,
    ScalingGroupOrderByGQL,
    ScalingGroupOrderFieldGQL,
    ScalingGroupV2GQL,
)

__all__ = (
    # Types
    "ScalingGroupV2GQL",
    "ScalingGroupFilterGQL",
    "ScalingGroupOrderByGQL",
    "ScalingGroupOrderFieldGQL",
    # Resolvers
    "scaling_groups_v2",
    "all_scaling_groups_v2",
)
