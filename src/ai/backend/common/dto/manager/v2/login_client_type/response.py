"""Response DTOs for login_client_type v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "SearchLoginClientTypesPayload",
    "CreateLoginClientTypePayload",
    "DeleteLoginClientTypePayload",
    "LoginClientTypeNode",
    "UpdateLoginClientTypePayload",
)


class LoginClientTypeNode(BaseResponseModel):
    """Node model representing a login client type entity."""

    id: UUID = Field(description="Login client type UUID.")
    name: str = Field(description="Unique login client type name.")
    description: str | None = Field(description="Optional description.")
    created_at: datetime = Field(description="Creation timestamp (UTC).")
    modified_at: datetime = Field(description="Last modification timestamp (UTC).")


class CreateLoginClientTypePayload(BaseResponseModel):
    """Payload for login client type creation."""

    login_client_type: LoginClientTypeNode = Field(description="Created login client type.")


class UpdateLoginClientTypePayload(BaseResponseModel):
    """Payload for login client type update."""

    login_client_type: LoginClientTypeNode = Field(description="Updated login client type.")


class DeleteLoginClientTypePayload(BaseResponseModel):
    """Payload for login client type deletion."""

    id: UUID = Field(description="UUID of the deleted login client type.")


class SearchLoginClientTypesPayload(BaseResponseModel):
    """Payload for paginated login client type search results."""

    items: list[LoginClientTypeNode] = Field(description="Login client type nodes.")
    total_count: int = Field(description="Total count matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
