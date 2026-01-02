"""CreatorSpec for deployment auto-scaling policy creation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from typing_extensions import override

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
)
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DeploymentAutoScalingPolicyCreatorSpec(CreatorSpec[DeploymentAutoScalingPolicyRow]):
    """CreatorSpec for deployment auto-scaling policy creation.

    Each endpoint can have at most one auto-scaling policy (1:1 relationship).
    The policy supports dual thresholds for hysteresis-based scaling.
    """

    endpoint_id: uuid.UUID
    min_replicas: int
    max_replicas: int
    metric_source: Optional[AutoScalingMetricSource]
    metric_name: Optional[str]
    comparator: Optional[AutoScalingMetricComparator]
    scale_up_threshold: Optional[Decimal]
    scale_down_threshold: Optional[Decimal]
    scale_up_step_size: int
    scale_down_step_size: int
    cooldown_seconds: int

    @override
    def build_row(self) -> DeploymentAutoScalingPolicyRow:
        return DeploymentAutoScalingPolicyRow(
            endpoint=self.endpoint_id,
            min_replicas=self.min_replicas,
            max_replicas=self.max_replicas,
            metric_source=self.metric_source,
            metric_name=self.metric_name,
            comparator=self.comparator,
            scale_up_threshold=self.scale_up_threshold,
            scale_down_threshold=self.scale_down_threshold,
            scale_up_step_size=self.scale_up_step_size,
            scale_down_step_size=self.scale_down_step_size,
            cooldown_seconds=self.cooldown_seconds,
        )
