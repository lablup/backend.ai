"""
Request DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import RoleSource, RoleStatus

__all__ = ("CreateRoleRequest",)


class CreateRoleRequest(BaseRequestModel):
    """Request to create a role."""

    name: str = Field(description="Role name")
    source: RoleSource = Field(default=RoleSource.CUSTOM, description="Role source")
    status: RoleStatus = Field(default=RoleStatus.ACTIVE, description="Role status")
    description: Optional[str] = Field(default=None, description="Role description")
