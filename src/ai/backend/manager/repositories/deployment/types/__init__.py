"""Type definitions for deployment repository."""

from .auto_scaling import AutoScalingRuleData
from .endpoint import (
    EndpointCreationArgs,
    EndpointData,
    EndpointHealthCheckContext,
    RouteData,
    RouteServiceDiscoveryInfo,
)
from .source import HealthCheckSource

__all__ = [
    "EndpointCreationArgs",
    "EndpointData",
    "EndpointHealthCheckContext",
    "RouteData",
    "RouteServiceDiscoveryInfo",
    "AutoScalingRuleData",
    "HealthCheckSource",
]
