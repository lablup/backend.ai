from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource


# Dataclasses for auto scaling rules used in Model Service (legacy)
@dataclass
class AutoScalingCondition:
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator


@dataclass
class AutoScalingAction:
    step_size: int
    cooldown_seconds: int
    min_replicas: Optional[int] = None
    max_replicas: Optional[int] = None


@dataclass
class AutoScalingRuleCreator:
    condition: AutoScalingCondition
    action: AutoScalingAction


@dataclass
class AutoScalingRule:
    id: UUID
    condition: AutoScalingCondition
    action: AutoScalingAction
    created_at: datetime
    last_triggered_at: Optional[datetime]


# Dataclasses for auto scaling rules used in Model Deployment
@dataclass
class ModelDeploymentAutoScalingRuleCreator:
    model_deployment_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Optional[Decimal]
    max_threshold: Optional[Decimal]
    step_size: int
    time_window: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]


@dataclass
class ModelDeploymentAutoScalingRule:
    id: UUID
    model_deployment_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Optional[Decimal]
    max_threshold: Optional[Decimal]
    step_size: int
    time_window: int
    min_replicas: Optional[int]
    max_replicas: Optional[int]
