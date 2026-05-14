"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import (
    EndpointCreationArgs,
    EndpointData,
    ProjectDeploymentSearchScope,
    RouteData,
    RouteServiceDiscoveryInfo,
    RouteSessionInfo,
    RouteSessionKernelInfo,
)

__all__ = [
    "AutoScalingRuleData",
    "EndpointCreationArgs",
    "EndpointData",
    "ProjectDeploymentSearchScope",
    "RouteData",
    "RouteServiceDiscoveryInfo",
    "RouteSessionInfo",
    "RouteSessionKernelInfo",
]
