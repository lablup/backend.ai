"""
Response DTOs for keypair system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CreateKeyPairResponse",
    "DeleteKeyPairResponse",
    "GetKeyPairResponse",
    "KeyPairDTO",
    "PaginationInfo",
    "SearchKeyPairsResponse",
    "UpdateKeyPairResponse",
)


class KeyPairDTO(BaseModel):
    """DTO for keypair data."""

    access_key: str = Field(description="Access key")
    secret_key: str = Field(description="Secret key")
    user_id: str | None = Field(default=None, description="User email")
    user_uuid: uuid.UUID = Field(description="User UUID")
    is_active: bool = Field(description="Whether the keypair is active")
    is_admin: bool = Field(description="Whether the keypair has admin privileges")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    modified_at: datetime | None = Field(default=None, description="Last modification timestamp")
    last_used: datetime | None = Field(default=None, description="Last used timestamp")
    resource_policy: str = Field(description="Resource policy name")
    rate_limit: int = Field(description="API rate limit")
    num_queries: int = Field(description="Number of queries made")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class CreateKeyPairResponse(BaseResponseModel):
    """Response for creating a keypair."""

    keypair: KeyPairDTO = Field(description="Created keypair")


class GetKeyPairResponse(BaseResponseModel):
    """Response for getting a keypair."""

    keypair: KeyPairDTO = Field(description="Keypair data")


class SearchKeyPairsResponse(BaseResponseModel):
    """Response for searching keypairs."""

    keypairs: list[KeyPairDTO] = Field(description="List of keypairs")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateKeyPairResponse(BaseResponseModel):
    """Response for updating a keypair."""

    keypair: KeyPairDTO = Field(description="Updated keypair")


class DeleteKeyPairResponse(BaseResponseModel):
    """Response for deleting keypairs."""

    deleted: bool = Field(description="Whether the keypairs were deleted")
