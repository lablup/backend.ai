"""
Response DTOs for auto-scaling rule system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import AutoScalingMetricSource

__all__ = (
    "AutoScalingRuleDTO",
    "CreateAutoScalingRuleResponse",
    "DeleteAutoScalingRuleResponse",
    "GetAutoScalingRuleResponse",
    "PaginationInfo",
    "SearchAutoScalingRulesResponse",
    "UpdateAutoScalingRuleResponse",
)


class AutoScalingRuleDTO(BaseModel):
    """DTO for auto-scaling rule data."""

    id: UUID = Field(description="Auto-scaling rule ID")
    model_deployment_id: UUID = Field(description="Associated deployment ID")
    metric_source: AutoScalingMetricSource = Field(description="Metric source")
    metric_name: str = Field(description="Metric name")
    min_threshold: Decimal | None = Field(default=None, description="Minimum threshold")
    max_threshold: Decimal | None = Field(default=None, description="Maximum threshold")
    step_size: int = Field(description="Step size for scaling")
    time_window: int = Field(description="Time window in seconds")
    min_replicas: int | None = Field(default=None, description="Minimum replicas")
    max_replicas: int | None = Field(default=None, description="Maximum replicas")
    created_at: datetime = Field(description="Creation timestamp")
    last_triggered_at: datetime = Field(description="Last triggered timestamp")


class CreateAutoScalingRuleResponse(BaseResponseModel):
    """Response for creating an auto-scaling rule."""

    auto_scaling_rule: AutoScalingRuleDTO = Field(description="Created auto-scaling rule")


class GetAutoScalingRuleResponse(BaseResponseModel):
    """Response for getting an auto-scaling rule."""

    auto_scaling_rule: AutoScalingRuleDTO = Field(description="Auto-scaling rule data")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class SearchAutoScalingRulesResponse(BaseResponseModel):
    """Response for searching auto-scaling rules."""

    auto_scaling_rules: list[AutoScalingRuleDTO] = Field(description="List of auto-scaling rules")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateAutoScalingRuleResponse(BaseResponseModel):
    """Response for updating an auto-scaling rule."""

    auto_scaling_rule: AutoScalingRuleDTO = Field(description="Updated auto-scaling rule")


class DeleteAutoScalingRuleResponse(BaseResponseModel):
    """Response for deleting an auto-scaling rule."""

    deleted: bool = Field(description="Whether the rule was deleted")
