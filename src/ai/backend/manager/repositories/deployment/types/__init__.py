"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import EndpointCreationArgs, EndpointData, RouteData

__all__ = [
    "EndpointCreationArgs",
    "EndpointData",
    "RouteData",
    "AutoScalingRuleData",
]
