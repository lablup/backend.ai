from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.retention_policy.types import RetentionPolicyOrderField
from ai.backend.common.identifier.retention_policy import RetentionPolicyID


class CreateRetentionPolicyInput(BaseRequestModel):
    category: RetentionCategory = Field(
        description="Retention category, validated against the fixed catalog."
    )
    retention_period_days: int = Field(
        ge=1,
        description="Retention period in days; records older than now - period are purged.",
    )
    enabled: bool = Field(default=True, description="Whether this policy is active.")


class UpdateRetentionPolicyInput(BaseRequestModel):
    id: RetentionPolicyID = Field(description="Retention policy ID.")
    category: RetentionCategory | None = Field(
        default=None,
        description="New category, validated against the catalog; None = no change.",
    )
    retention_period_days: int | None = Field(
        default=None, ge=1, description="New retention period in days; None = no change."
    )
    enabled: bool | None = Field(default=None, description="Toggle enabled; None = no change.")


class RetentionPolicyFilter(BaseRequestModel):
    category: RetentionCategory | None = Field(default=None, description="Filter by category.")
    enabled: bool | None = Field(default=None, description="Filter by enabled flag.")


class RetentionPolicyOrder(BaseRequestModel):
    field: RetentionPolicyOrderField
    direction: OrderDirection = OrderDirection.ASC


class SearchRetentionPoliciesInput(BaseRequestModel):
    filter: RetentionPolicyFilter | None = Field(default=None)
    order: list[RetentionPolicyOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
