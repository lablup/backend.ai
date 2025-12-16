"""
Response DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("RevokeRoleResponse",)


class RevokeRoleResponse(BaseResponseModel):
    """Response for revoking a role from a user."""

    user_role_id: UUID = Field(description="ID of the revoked user-role association")
    user_id: UUID = Field(description="User ID")
    role_id: UUID = Field(description="Role ID")
