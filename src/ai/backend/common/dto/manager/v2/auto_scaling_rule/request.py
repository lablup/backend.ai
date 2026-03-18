"""
Request DTOs for auto-scaling rule DTO v2.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

from .types import AutoScalingMetricSource, AutoScalingRuleOrderField, OrderDirection

__all__ = (
    "AutoScalingRuleFilter",
    "AutoScalingRuleOrder",
    "CreateAutoScalingRuleInput",
    "DeleteAutoScalingRuleInput",
    "SearchAutoScalingRulesInput",
    "UpdateAutoScalingRuleInput",
)


class CreateAutoScalingRuleInput(BaseRequestModel):
    """Input for creating an auto-scaling rule."""

    model_deployment_id: UUID = Field(description="ID of the deployment to attach the rule to")
    metric_source: AutoScalingMetricSource = Field(
        description="Source of the metric (e.g. KERNEL, INFERENCE_FRAMEWORK)"
    )
    metric_name: str = Field(min_length=1, description="Name of the metric to monitor")
    min_threshold: Decimal | None = Field(default=None, description="Minimum threshold for scaling")
    max_threshold: Decimal | None = Field(default=None, description="Maximum threshold for scaling")
    step_size: int = Field(ge=1, description="Step size for scaling")
    time_window: int = Field(ge=1, description="Time window in seconds for scaling evaluation")
    min_replicas: int | None = Field(default=None, ge=0, description="Minimum number of replicas")
    max_replicas: int | None = Field(default=None, ge=1, description="Maximum number of replicas")


class UpdateAutoScalingRuleInput(BaseRequestModel):
    """Input for updating an auto-scaling rule.

    Fields default to SENTINEL (no change). Set a field to None to clear it.
    Fields that cannot be cleared use None to signal no change.
    """

    metric_source: AutoScalingMetricSource | None = Field(
        default=None, description="Updated metric source. None means no change."
    )
    metric_name: str | None = Field(
        default=None, description="Updated metric name. None means no change."
    )
    min_threshold: Decimal | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated minimum threshold. SENTINEL = no change, None = clear.",
    )
    max_threshold: Decimal | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated maximum threshold. SENTINEL = no change, None = clear.",
    )
    step_size: int | None = Field(
        default=None, description="Updated step size. None means no change."
    )
    time_window: int | None = Field(
        default=None, description="Updated time window in seconds. None means no change."
    )
    min_replicas: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated minimum replicas. SENTINEL = no change, None = clear.",
    )
    max_replicas: int | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated maximum replicas. SENTINEL = no change, None = clear.",
    )


class DeleteAutoScalingRuleInput(BaseRequestModel):
    """Input for deleting an auto-scaling rule."""

    id: UUID = Field(description="ID of the auto-scaling rule to delete")


class AutoScalingRuleFilter(BaseRequestModel):
    """Filter conditions for auto-scaling rule search."""

    model_deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")


class AutoScalingRuleOrder(BaseRequestModel):
    """Order specification for auto-scaling rule search."""

    field: AutoScalingRuleOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchAutoScalingRulesInput(BaseRequestModel):
    """Input for searching auto-scaling rules with filters, orders, and pagination."""

    filter: AutoScalingRuleFilter | None = Field(default=None, description="Filter conditions")
    order: list[AutoScalingRuleOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
