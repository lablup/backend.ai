"""
Common DTOs for RBAC system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import UpdateRoleRequest
from .response import RoleDTO, UpdateRoleResponse
from .types import RoleSource, RoleStatus

__all__ = (
    # Types
    "RoleSource",
    "RoleStatus",
    # Request DTOs
    "UpdateRoleRequest",
    # Response DTOs
    "RoleDTO",
    "UpdateRoleResponse",
)
