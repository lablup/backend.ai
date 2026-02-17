"""
Request DTOs for auto-scaling rule system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.types import AutoScalingMetricSource

from .types import (
    AutoScalingRuleOrderField,
    OrderDirection,
)

__all__ = (
    "AutoScalingRuleFilter",
    "AutoScalingRuleOrder",
    "CreateAutoScalingRuleRequest",
    "DeleteAutoScalingRuleRequest",
    "SearchAutoScalingRulesRequest",
    "UpdateAutoScalingRuleRequest",
)


class CreateAutoScalingRuleRequest(BaseRequestModel):
    """Request to create an auto-scaling rule."""

    model_deployment_id: UUID = Field(description="ID of the deployment to attach the rule to")
    metric_source: AutoScalingMetricSource = Field(
        description="Source of the metric (e.g. KERNEL, INFERENCE_FRAMEWORK)"
    )
    metric_name: str = Field(description="Name of the metric to monitor")
    min_threshold: Decimal | None = Field(default=None, description="Minimum threshold for scaling")
    max_threshold: Decimal | None = Field(default=None, description="Maximum threshold for scaling")
    step_size: int = Field(description="Step size for scaling")
    time_window: int = Field(description="Time window in seconds for scaling evaluation")
    min_replicas: int | None = Field(default=None, description="Minimum number of replicas")
    max_replicas: int | None = Field(default=None, description="Maximum number of replicas")


class UpdateAutoScalingRuleRequest(BaseRequestModel):
    """Request to update an auto-scaling rule."""

    metric_source: AutoScalingMetricSource | None = Field(
        default=None, description="Updated metric source"
    )
    metric_name: str | None = Field(default=None, description="Updated metric name")
    min_threshold: Decimal | None = Field(default=None, description="Updated minimum threshold")
    max_threshold: Decimal | None = Field(default=None, description="Updated maximum threshold")
    step_size: int | None = Field(default=None, description="Updated step size")
    time_window: int | None = Field(default=None, description="Updated time window in seconds")
    min_replicas: int | None = Field(default=None, description="Updated minimum replicas")
    max_replicas: int | None = Field(default=None, description="Updated maximum replicas")


class AutoScalingRuleFilter(BaseRequestModel):
    """Filter for auto-scaling rules."""

    model_deployment_id: UUID | None = Field(default=None, description="Filter by deployment ID")


class AutoScalingRuleOrder(BaseRequestModel):
    """Order specification for auto-scaling rules."""

    field: AutoScalingRuleOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchAutoScalingRulesRequest(BaseRequestModel):
    """Request body for searching auto-scaling rules with filters, orders, and pagination."""

    filter: AutoScalingRuleFilter | None = Field(default=None, description="Filter conditions")
    order: list[AutoScalingRuleOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class DeleteAutoScalingRuleRequest(BaseRequestModel):
    """Request to delete an auto-scaling rule."""

    rule_id: UUID = Field(description="ID of the auto-scaling rule to delete")
