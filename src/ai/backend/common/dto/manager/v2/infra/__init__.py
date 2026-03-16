"""
Infra DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.infra.request import (
    CheckPresetsInput,
    GetWSProxyVersionInput,
    ListPresetsInput,
    ListScalingGroupsInput,
    UsagePerMonthInput,
    UsagePerPeriodInput,
    WatcherAgentInput,
)
from ai.backend.common.dto.manager.v2.infra.response import (
    CheckPresetsPayload,
    ContainerRegistriesPayload,
    ListPresetsPayload,
    ListScalingGroupsPayload,
    ResourcePresetNode,
    ScalingGroupNode,
    UsagePayload,
    WatcherActionPayload,
    WatcherStatusPayload,
    WSProxyVersionPayload,
)
from ai.backend.common.dto.manager.v2.infra.types import (
    AcceleratorMetadataInfo,
    InfraOrderField,
    NumberFormatInfo,
    OrderDirection,
)

__all__ = (
    # Types
    "AcceleratorMetadataInfo",
    "InfraOrderField",
    "NumberFormatInfo",
    "OrderDirection",
    # Input models (request)
    "CheckPresetsInput",
    "GetWSProxyVersionInput",
    "ListPresetsInput",
    "ListScalingGroupsInput",
    "UsagePerMonthInput",
    "UsagePerPeriodInput",
    "WatcherAgentInput",
    # Node and Payload models (response)
    "CheckPresetsPayload",
    "ContainerRegistriesPayload",
    "ListPresetsPayload",
    "ListScalingGroupsPayload",
    "ResourcePresetNode",
    "ScalingGroupNode",
    "UsagePayload",
    "WSProxyVersionPayload",
    "WatcherActionPayload",
    "WatcherStatusPayload",
)
