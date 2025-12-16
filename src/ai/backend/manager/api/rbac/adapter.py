"""
Adapter to convert RBAC data models to DTOs.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.rbac import RoleDTO
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData

__all__ = ("RoleAdapter",)


class RoleAdapter:
    """Adapter for converting role data to DTOs."""

    def convert_to_dto(self, data: RoleData | RoleDetailData) -> RoleDTO:
        """Convert RoleData to DTO."""
        return RoleDTO(
            id=data.id,
            name=data.name,
            source=data.source,
            status=data.status,
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            description=data.description,
        )
