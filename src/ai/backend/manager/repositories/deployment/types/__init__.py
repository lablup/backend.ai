"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import EndpointCreationArgs, EndpointData, RouteData, RouteServiceDiscoveryInfo

__all__ = [
    "EndpointCreationArgs",
    "EndpointData",
    "RouteData",
    "RouteServiceDiscoveryInfo",
    "AutoScalingRuleData",
]
