"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import (
    DeploymentHistoryToCreate,
    EndpointCreationArgs,
    EndpointData,
    RouteData,
    RouteHistoryToCreate,
    RouteServiceDiscoveryInfo,
    RouteSessionInfo,
    RouteSessionKernelInfo,
)

__all__ = [
    "AutoScalingRuleData",
    "DeploymentHistoryToCreate",
    "EndpointCreationArgs",
    "EndpointData",
    "RouteData",
    "RouteHistoryToCreate",
    "RouteServiceDiscoveryInfo",
    "RouteSessionInfo",
    "RouteSessionKernelInfo",
]
