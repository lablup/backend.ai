"""
Common DTOs for RBAC system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import RevokeRoleRequest
from .response import RevokeRoleResponse

__all__ = (
    "RevokeRoleRequest",
    "RevokeRoleResponse",
)
