"""Response DTOs for the client IP masking DTO v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import ClientIPMaskingMode, ClientIPMaskingTarget

__all__ = (
    "AdminSearchClientIPMaskingPoliciesPayload",
    "ClientIPMaskingPolicyNode",
    "ClientIPMaskingPolicyPayload",
)


class ClientIPMaskingPolicyNode(BaseResponseModel):
    """Node model representing the masking set for one target."""

    id: UUID = Field(description="Policy ID")
    target_type: ClientIPMaskingTarget = Field(description="Which recorded client IP is governed")
    mode: ClientIPMaskingMode = Field(description="Masking applied before the address is stored")
    created_at: datetime = Field(description="Timestamp when the policy was first written")
    updated_at: datetime = Field(description="Timestamp when the policy was last changed")


class AdminSearchClientIPMaskingPoliciesPayload(BaseResponseModel):
    """Payload for the client IP masking policies search result (admin)."""

    items: list[ClientIPMaskingPolicyNode] = Field(description="Client IP masking policies")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")


class ClientIPMaskingPolicyPayload(BaseResponseModel):
    """Payload carrying the settled policy row."""

    policy: ClientIPMaskingPolicyNode = Field(description="The policy the operation left")
