"""
Response DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("AssignRoleResponse",)


class AssignRoleResponse(BaseResponseModel):
    """Response for assigning a role to a user."""

    user_id: UUID = Field(description="User ID")
    role_id: UUID = Field(description="Role ID")
    granted_by: Optional[UUID] = Field(default=None, description="ID of user who granted the role")
