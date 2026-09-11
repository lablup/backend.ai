"""
Request DTOs for auto-scaling rule DTO v2.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.tristate.unset import UNSET, Unset

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
    prometheus_query_preset_id: UUID | None = Field(
        default=None,
        description="ID of Prometheus query preset (required when metric_source is PROMETHEUS)",
    )


class UpdateAutoScalingRuleInput(BaseRequestModel):
    """Input for updating an auto-scaling rule.

    Every field defaults to UNSET (no change). Null clears only the nullable fields.
    """

    id: UUID = Field(description="ID of the auto-scaling rule to update")
    metric_source: AutoScalingMetricSource | None | Unset = Field(
        default=UNSET, description="Updated metric source. Omit to leave unchanged."
    )
    metric_name: str | None | Unset = Field(
        default=UNSET, description="Updated metric name. Omit to leave unchanged."
    )
    min_threshold: Decimal | None | Unset = Field(
        default=UNSET,
        description="Updated minimum threshold. Omit to leave unchanged; null clears.",
    )
    max_threshold: Decimal | None | Unset = Field(
        default=UNSET,
        description="Updated maximum threshold. Omit to leave unchanged; null clears.",
    )
    step_size: int | None | Unset = Field(
        default=UNSET, description="Updated step size. Omit to leave unchanged."
    )
    time_window: int | None | Unset = Field(
        default=UNSET, description="Updated time window in seconds. Omit to leave unchanged."
    )
    min_replicas: int | None | Unset = Field(
        default=UNSET,
        description="Updated minimum replicas. Omit to leave unchanged; null clears.",
    )
    max_replicas: int | None | Unset = Field(
        default=UNSET,
        description="Updated maximum replicas. Omit to leave unchanged; null clears.",
    )
    prometheus_query_preset_id: UUID | None | Unset = Field(
        default=UNSET,
        description="Updated Prometheus query preset ID. Omit to leave unchanged; null clears.",
    )


class DeleteAutoScalingRuleInput(BaseRequestModel):
    """Input for deleting an auto-scaling rule."""

    id: UUID = Field(description="ID of the auto-scaling rule to delete")


class BulkDeleteAutoScalingRulesInput(BaseRequestModel):
    """Input for bulk deleting auto-scaling rules."""

    ids: list[UUID] = Field(description="List of auto-scaling rule UUIDs to delete.")


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
