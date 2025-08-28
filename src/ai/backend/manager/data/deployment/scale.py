from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource


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
