"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import EndpointCreationArgs, EndpointData, EndpointWithRoutesData, RouteData

__all__ = [
    "EndpointCreationArgs",
    "EndpointData",
    "EndpointWithRoutesData",
    "RouteData",
    "AutoScalingRuleData",
]
