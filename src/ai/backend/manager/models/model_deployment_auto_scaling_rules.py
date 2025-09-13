import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    DecimalType,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ModelDeploymentAutoScalingRuleRow",)


def _get_auto_scaling_rule_deployment_join_cond():
    from .model_deployment import ModelDeploymentRow

    return foreign(ModelDeploymentAutoScalingRuleRow.model_deployment_id) == ModelDeploymentRow.id


class ModelDeploymentAutoScalingRuleRow(Base):
    __tablename__ = "model_deployment_auto_scaling_rules"

    id = IDColumn("id")

    model_deployment_id = sa.Column(
        "model_deployment_id",
        GUID,
        nullable=False,
    )
    metric_source = sa.Column("metric_source", sa.String, nullable=False)
    metric_name = sa.Column("metric_name", sa.String, nullable=False)
    min_threshold = sa.Column("min_threshold", DecimalType(), nullable=True)
    max_threshold = sa.Column("max_threshold", DecimalType(), nullable=True)
    step_size = sa.Column("step_size", sa.Integer, nullable=False)
    time_window = sa.Column("time_window", sa.Integer, nullable=False)
    min_replicas = sa.Column("min_replicas", sa.Integer, nullable=True)
    max_replicas = sa.Column("max_replicas", sa.Integer, nullable=True)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    last_triggered_at = sa.Column(
        "last_triggered_at",
        sa.DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    model_deployment_row = relationship(
        "ModelDeploymentRow",
        back_populates="auto_scaling_rule_rows",
        primaryjoin=_get_auto_scaling_rule_deployment_join_cond,
    )

    def __init__(
        self,
        metric_source: str,
        metric_name: str,
        step_size: int,
        time_window: int,
        last_triggered_at: datetime,
        model_deployment_id: Optional[uuid.UUID] = None,
        min_threshold: Optional[Decimal] = None,
        max_threshold: Optional[Decimal] = None,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.model_deployment_id = model_deployment_id
        self.metric_source = metric_source
        self.metric_name = metric_name
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.step_size = step_size
        self.time_window = time_window
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.created_at = created_at
        self.last_triggered_at = last_triggered_at

    def __str__(self) -> str:
        return (
            f"ModelDeploymentAutoScalingRuleRow("
            f"id: {self.id}, "
            f"model_deployment_id: {self.model_deployment_id}, "
            f"metric_name: {self.metric_name}, "
            f"min_threshold: {self.min_threshold}, "
            f"max_threshold: {self.max_threshold}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
