"""
Response DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import RoleSource, RoleStatus

__all__ = (
    "RoleDTO",
    "CreateRoleResponse",
)


class RoleDTO(BaseModel):
    """DTO for role data."""

    id: UUID = Field(description="Role ID")
    name: str = Field(description="Role name")
    source: RoleSource = Field(description="Role source")
    status: RoleStatus = Field(description="Role status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")
    description: Optional[str] = Field(default=None, description="Role description")


class CreateRoleResponse(BaseResponseModel):
    """Response for creating a role."""

    role: RoleDTO = Field(description="Created role")
