from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.retention.types import RetentionCategory


class RetentionPolicyNode(BaseResponseModel):
    id: UUID = Field(description="Retention policy ID.")
    category: RetentionCategory = Field(description="Retention category.")
    retention_period_days: int = Field(description="Retention period in days.")
    enabled: bool = Field(description="Whether this policy is active.")
    last_swept_at: datetime | None = Field(
        default=None, description="When this policy was last swept (read-only observability field)."
    )
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime = Field(description="Last update timestamp.")


class CreateRetentionPolicyPayload(BaseResponseModel):
    policy: RetentionPolicyNode = Field(description="The created retention policy.")


class UpdateRetentionPolicyPayload(BaseResponseModel):
    policy: RetentionPolicyNode = Field(description="The updated retention policy.")


class DeleteRetentionPolicyPayload(BaseResponseModel):
    id: UUID = Field(description="ID of the deleted retention policy.")


class PurgeRetentionPolicyPayload(BaseResponseModel):
    id: UUID = Field(description="ID of the purged retention policy.")


class SearchRetentionPoliciesPayload(BaseResponseModel):
    items: list[RetentionPolicyNode] = Field(description="List of retention policies.")
    total_count: int = Field(description="Total number of matching items.")
    has_next_page: bool = Field(description="Whether there are more items after.")
    has_previous_page: bool = Field(description="Whether there are more items before.")
