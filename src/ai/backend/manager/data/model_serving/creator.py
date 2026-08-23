"""Data containers for model serving operations.

These are data containers, not write specs; row creation goes through the specs in
``models/endpoint/creators.py``.
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
