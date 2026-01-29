from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
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
    min_replicas: int | None = None
    max_replicas: int | None = None


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
    last_triggered_at: datetime | None


# Dataclasses for auto scaling rules used in Model Deployment
@dataclass
class ModelDeploymentAutoScalingRuleCreator:
    model_deployment_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Decimal | None
    max_threshold: Decimal | None
    step_size: int
    time_window: int
    min_replicas: int | None
    max_replicas: int | None


@dataclass
class ModelDeploymentAutoScalingRule:
    id: UUID
    model_deployment_id: UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    min_threshold: Decimal | None
    max_threshold: Decimal | None
    step_size: int
    time_window: int
    min_replicas: int | None
    max_replicas: int | None
