"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import EndpointCreationArgs, EndpointData, RouteData, RouteServiceDiscoveryInfo
from .source import HealthCheckSource

__all__ = [
    "EndpointCreationArgs",
    "EndpointData",
    "RouteData",
    "RouteServiceDiscoveryInfo",
    "AutoScalingRuleData",
    "HealthCheckSource",
]
