"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import (
    EndpointCreationArgs,
    EndpointData,
    RouteAppProxySyncInfo,
    RouteData,
    RouteServiceDiscoveryInfo,
)

__all__ = [
    "AutoScalingRuleData",
    "EndpointCreationArgs",
    "EndpointData",
    "RouteAppProxySyncInfo",
    "RouteData",
    "RouteServiceDiscoveryInfo",
]
