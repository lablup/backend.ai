"""Types for deployment repository."""

from .endpoint import EndpointConfig, EndpointData
from .health import HealthData
from .replica import ReplicaData, ReplicaUpdate
from .route import RouteData
from .scaling import AutoScalingRuleData, ScalingData

__all__ = [
    "EndpointData",
    "EndpointConfig",
    "RouteData",
    "ReplicaData",
    "ReplicaUpdate",
    "ScalingData",
    "AutoScalingRuleData",
    "HealthData",
]
