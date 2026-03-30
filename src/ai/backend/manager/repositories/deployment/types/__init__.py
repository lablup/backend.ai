"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import EndpointCreationArgs, EndpointData, RouteData, RouteServiceDiscoveryInfo

__all__ = [
    "AutoScalingRuleData",
    "EndpointCreationArgs",
    "EndpointData",
    "RouteData",
    "RouteServiceDiscoveryInfo",
]
