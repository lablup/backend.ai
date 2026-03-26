"""
Response DTOs for auto-scaling rule DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

from .types import AutoScalingMetricSource

__all__ = (
    "AutoScalingRuleNode",
    "CreateAutoScalingRulePayload",
    "DeleteAutoScalingRulePayload",
    "GetAutoScalingRulePayload",
    "SearchAutoScalingRulesPayload",
    "UpdateAutoScalingRulePayload",
)


class AutoScalingRuleNode(BaseResponseModel):
    """Node model representing an auto-scaling rule entity."""

    id: UUID = Field(description="Auto-scaling rule ID")
    model_deployment_id: UUID = Field(description="Associated deployment ID")
    metric_source: AutoScalingMetricSource = Field(description="Source of the metric")
    metric_name: str = Field(description="Name of the metric to monitor")
    min_threshold: Decimal | None = Field(default=None, description="Minimum threshold for scaling")
    max_threshold: Decimal | None = Field(default=None, description="Maximum threshold for scaling")
    step_size: int = Field(description="Step size for scaling")
    time_window: int = Field(description="Time window in seconds for scaling evaluation")
    min_replicas: int | None = Field(default=None, description="Minimum number of replicas")
    max_replicas: int | None = Field(default=None, description="Maximum number of replicas")
    created_at: datetime = Field(description="Creation timestamp")
    last_triggered_at: datetime = Field(description="Last triggered timestamp")


class CreateAutoScalingRulePayload(BaseResponseModel):
    """Payload for auto-scaling rule creation mutation result."""

    rule: AutoScalingRuleNode = Field(description="Created auto-scaling rule")


class GetAutoScalingRulePayload(BaseResponseModel):
    """Payload for getting a single auto-scaling rule."""

    rule: AutoScalingRuleNode = Field(description="Auto-scaling rule data")


class SearchAutoScalingRulesPayload(BaseResponseModel):
    """Payload for searching auto-scaling rules."""

    items: list[AutoScalingRuleNode] = Field(description="List of auto-scaling rules")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateAutoScalingRulePayload(BaseResponseModel):
    """Payload for auto-scaling rule update mutation result."""

    rule: AutoScalingRuleNode = Field(description="Updated auto-scaling rule")


class DeleteAutoScalingRulePayload(BaseResponseModel):
    """Payload for auto-scaling rule deletion mutation result."""

    id: UUID = Field(description="ID of the deleted auto-scaling rule")
