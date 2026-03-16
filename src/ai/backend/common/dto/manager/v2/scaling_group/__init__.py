"""
Scaling group DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.scaling_group.request import (
    PreemptionConfigInput,
    UpdateScalingGroupInput,
)
from ai.backend.common.dto.manager.v2.scaling_group.response import (
    PreemptionConfigInfo,
    ScalingGroupMetadataInfo,
    ScalingGroupNetworkInfo,
    ScalingGroupNode,
    ScalingGroupSchedulerInfo,
    ScalingGroupStatusInfo,
    UpdateScalingGroupPayload,
)
from ai.backend.common.dto.manager.v2.scaling_group.types import (
    OrderDirection,
    PreemptionMode,
    PreemptionOrder,
    ScalingGroupOrderField,
    SchedulerType,
)

__all__ = (
    # Types
    "OrderDirection",
    "PreemptionMode",
    "PreemptionOrder",
    "ScalingGroupOrderField",
    "SchedulerType",
    # Input models (request)
    "PreemptionConfigInput",
    "UpdateScalingGroupInput",
    # Node and Payload models (response)
    "PreemptionConfigInfo",
    "ScalingGroupMetadataInfo",
    "ScalingGroupNetworkInfo",
    "ScalingGroupNode",
    "ScalingGroupSchedulerInfo",
    "ScalingGroupStatusInfo",
    "UpdateScalingGroupPayload",
)
