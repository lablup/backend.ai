"""
Request DTOs for keypair system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    KeyPairOrderField,
    OrderDirection,
)

__all__ = (
    "ActivateKeyPairRequest",
    "CreateKeyPairRequest",
    "DeactivateKeyPairRequest",
    "DeleteKeyPairRequest",
    "KeyPairFilter",
    "KeyPairOrder",
    "SearchKeyPairsRequest",
    "StringFilter",
    "UpdateKeyPairRequest",
)


class CreateKeyPairRequest(BaseRequestModel):
    """Request to create a keypair."""

    user_id: str = Field(description="User email or ID to associate with the keypair")
    is_active: bool = Field(default=True, description="Whether the keypair is active")
    is_admin: bool = Field(default=False, description="Whether the keypair has admin privileges")
    resource_policy: str = Field(
        default="default", description="Name of the resource policy to apply"
    )
    rate_limit: int = Field(default=0, description="API rate limit for this keypair")


class UpdateKeyPairRequest(BaseRequestModel):
    """Request to update a keypair."""

    is_active: bool | None = Field(default=None, description="Updated active status")
    is_admin: bool | None = Field(default=None, description="Updated admin status")
    resource_policy: str | None = Field(default=None, description="Updated resource policy name")
    rate_limit: int | None = Field(default=None, description="Updated rate limit")


class KeyPairFilter(BaseRequestModel):
    """Filter for keypairs."""

    user_id: StringFilter | None = Field(default=None, description="Filter by user email")
    access_key: StringFilter | None = Field(default=None, description="Filter by access key")
    is_active: bool | None = Field(default=None, description="Filter by active status")
    is_admin: bool | None = Field(default=None, description="Filter by admin status")
    resource_policy: StringFilter | None = Field(
        default=None, description="Filter by resource policy name"
    )


class KeyPairOrder(BaseRequestModel):
    """Order specification for keypairs."""

    field: KeyPairOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchKeyPairsRequest(BaseRequestModel):
    """Request body for searching keypairs with filters, orders, and pagination."""

    filter: KeyPairFilter | None = Field(default=None, description="Filter conditions")
    order: list[KeyPairOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class DeleteKeyPairRequest(BaseRequestModel):
    """Request to delete keypairs."""

    access_keys: list[str] = Field(description="List of access keys to delete")


class ActivateKeyPairRequest(BaseRequestModel):
    """Request to activate a keypair (empty body, access_key from path)."""


class DeactivateKeyPairRequest(BaseRequestModel):
    """Request to deactivate a keypair (empty body, access_key from path)."""
