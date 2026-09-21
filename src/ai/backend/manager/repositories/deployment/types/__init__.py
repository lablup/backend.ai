"""Type definitions for deployment repository."""

from ai.backend.manager.data.deployment.types import RouteData

from .auto_scaling import AutoScalingRuleData
from .endpoint import (
    DeploymentHistoryToCreate,
    EndpointCreationArgs,
    EndpointData,
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
