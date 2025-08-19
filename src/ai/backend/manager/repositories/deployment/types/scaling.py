"""Scaling types for deployment repository."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
)

from .endpoint import EndpointData
from .route import RouteData


@dataclass(frozen=True)
class AutoScalingRuleData:
    """Data representing an auto-scaling rule."""

    id: UUID
    endpoint_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: Decimal
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]
    enabled: bool = True


@dataclass(frozen=True)
class ScalingData:
    """Data required for scaling decisions."""

    endpoint: EndpointData
    routes: list[RouteData]
    metrics: dict[str, float]
    rules: list[AutoScalingRuleData]
    last_scaling_time: Optional[str] = None
