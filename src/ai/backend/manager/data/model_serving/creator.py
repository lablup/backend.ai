"""Data containers for model serving operations.

Note: These are data containers, not CreatorSpec implementations.
For row creation, use EndpointCreatorSpec from repositories/model_serving/creators.py
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
)


@dataclass
class EndpointAutoScalingRuleCreator:
    """Data container for endpoint auto scaling rule creation parameters.

    This is not a CreatorSpec - the repository extracts individual fields
    and creates the row directly without using CreatorSpec pattern.
    """

    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: int | None = None
    max_replicas: int | None = None
