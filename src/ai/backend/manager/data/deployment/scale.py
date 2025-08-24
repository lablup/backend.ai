from dataclasses import dataclass
from typing import Optional

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.manager.types import Creator


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
class AutoScalingRuleCreator(Creator):
    condition: AutoScalingCondition
    action: AutoScalingAction


@dataclass
class AutoScalingRule:
    condition: AutoScalingCondition
    action: AutoScalingAction
