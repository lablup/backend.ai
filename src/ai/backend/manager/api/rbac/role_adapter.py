"""
Adapters to convert RBAC DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.rbac import RoleDTO, UpdateRoleRequest
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData, RoleUpdateInput
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("RoleAdapter",)


class RoleAdapter(BaseFilterAdapter):
    """Adapter for converting role requests to repository queries."""

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

    def build_modifier(self, role_id: UUID, request: UpdateRoleRequest) -> RoleUpdateInput:
        """Convert update request to modifier."""

        if request.name is not None:
            name = OptionalState.update(request.name)
        else:
            name = OptionalState.nop()
        if request.source is not None:
            source = OptionalState.update(request.source)
        else:
            source = OptionalState.nop()
        if request.status is not None:
            status = OptionalState.update(request.status)
        else:
            status = OptionalState.nop()
        if request.description is not SENTINEL:
            description = TriState[str].from_graphql(request.description)
        else:
            description = TriState[str].nop()

        modifier = RoleUpdateInput(
            id=role_id,
            name=name,
            source=source,
            status=status,
            description=description,
        )
        return modifier
