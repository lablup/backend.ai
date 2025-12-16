"""
Request DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = ("AssignRoleRequest",)


class AssignRoleRequest(BaseRequestModel):
    """Request to assign a role to a user."""

    user_id: UUID = Field(description="User ID to assign the role to")
    role_id: UUID = Field(description="Role ID to assign")
    granted_by: Optional[UUID] = Field(
        default=None, description="User ID who granted this role assignment"
    )
