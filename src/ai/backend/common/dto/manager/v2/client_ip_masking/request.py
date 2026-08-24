"""Request DTOs for the client IP masking DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

from .types import ClientIPMaskingMode, ClientIPMaskingPolicyOrderField, ClientIPMaskingTarget

__all__ = (
    "AdminPurgeClientIPMaskingPolicyInput",
    "AdminSearchClientIPMaskingPoliciesInput",
    "AdminUpsertClientIPMaskingPolicyInput",
    "ClientIPMaskingPolicyFilter",
    "ClientIPMaskingPolicyOrder",
)


class ClientIPMaskingPolicyFilter(BaseRequestModel):
    target_type: ClientIPMaskingTarget | None = Field(
        default=None, description="Filter by the governed target."
    )
    mode: ClientIPMaskingMode | None = Field(default=None, description="Filter by masking mode.")


class ClientIPMaskingPolicyOrder(BaseRequestModel):
    field: ClientIPMaskingPolicyOrderField
    direction: OrderDirection = OrderDirection.ASC


class AdminSearchClientIPMaskingPoliciesInput(BaseRequestModel):
    """Read the masking set for every target."""

    filter: ClientIPMaskingPolicyFilter | None = Field(default=None)
    order: list[ClientIPMaskingPolicyOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)


class AdminUpsertClientIPMaskingPolicyInput(BaseRequestModel):
    """Set the masking one target gets."""

    target_type: ClientIPMaskingTarget = Field(description="Which recorded client IP to govern")
    mode: ClientIPMaskingMode = Field(description="Masking applied before the address is stored")


class AdminPurgeClientIPMaskingPolicyInput(BaseRequestModel):
    """Drop one target's policy so it falls back to the default."""

    id: UUID = Field(description="Policy ID")
