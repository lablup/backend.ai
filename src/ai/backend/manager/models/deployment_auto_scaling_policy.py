from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    DecimalType,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    pass

__all__ = ("DeploymentAutoScalingPolicyRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class DeploymentAutoScalingPolicyRow(Base):
    """
    Represents an auto-scaling policy for a deployment (K8s HPA equivalent).

    Each endpoint has at most one auto-scaling policy (1:1 relationship).
    The policy defines scale-up and scale-down thresholds separately,
    allowing for hysteresis-based scaling decisions.
    """

    __tablename__ = "deployment_auto_scaling_policies"

    __table_args__ = (
        sa.UniqueConstraint("endpoint", name="uq_deployment_auto_scaling_policies_endpoint"),
        sa.Index("ix_deployment_auto_scaling_policies_endpoint", "endpoint"),
    )

    id = IDColumn()
    endpoint = sa.Column("endpoint", GUID, nullable=False)

    # Replica bounds (always enforced)
    min_replicas = sa.Column(
        "min_replicas", sa.Integer, nullable=False, default=1, server_default="1"
    )
    max_replicas = sa.Column(
        "max_replicas", sa.Integer, nullable=False, default=10, server_default="10"
    )

    # Metric configuration
    metric_source = sa.Column(
        "metric_source",
        StrEnumType(AutoScalingMetricSource, use_name=False),
        nullable=True,
    )
    metric_name = sa.Column("metric_name", sa.Text, nullable=True)
    comparator = sa.Column(
        "comparator",
        StrEnumType(AutoScalingMetricComparator, use_name=False),
        nullable=True,
    )

    # Dual thresholds for hysteresis
    scale_up_threshold = sa.Column("scale_up_threshold", DecimalType(), nullable=True)
    scale_down_threshold = sa.Column("scale_down_threshold", DecimalType(), nullable=True)

    # Step sizes
    scale_up_step_size = sa.Column(
        "scale_up_step_size", sa.Integer, nullable=False, default=1, server_default="1"
    )
    scale_down_step_size = sa.Column(
        "scale_down_step_size", sa.Integer, nullable=False, default=1, server_default="1"
    )

    # Cooldown
    cooldown_seconds = sa.Column(
        "cooldown_seconds", sa.Integer, nullable=False, default=300, server_default="300"
    )
    last_scaled_at = sa.Column("last_scaled_at", sa.DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        onupdate=sa.func.now(),
        nullable=True,
    )

    # Relationships (without FK constraints)
    endpoint_row = relationship(
        "EndpointRow",
        back_populates="auto_scaling_policy",
        primaryjoin="foreign(DeploymentAutoScalingPolicyRow.endpoint) == EndpointRow.id",
        uselist=False,
    )

    def to_data(self) -> DeploymentAutoScalingPolicyData:
        """Convert to DeploymentAutoScalingPolicyData dataclass."""
        return DeploymentAutoScalingPolicyData(
            id=self.id,
            endpoint=self.endpoint,
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
            last_scaled_at=self.last_scaled_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


@dataclass
class DeploymentAutoScalingPolicyData:
    """Data class for DeploymentAutoScalingPolicyRow."""

    id: UUID
    endpoint: UUID
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
    last_scaled_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
