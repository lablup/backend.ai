"""Auto-scaling rule data types for deployment repository."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
)


@dataclass
class AutoScalingRuleData:
    """Data structure for auto-scaling rule."""

    rule_id: uuid.UUID
    endpoint_id: uuid.UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: Decimal
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: int | None = None
    max_replicas: int | None = None
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_triggered_at: datetime | None = None
