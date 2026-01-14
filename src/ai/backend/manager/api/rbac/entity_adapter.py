"""
Adapter for Entity API requests.
Handles conversion of request DTOs to BatchQuerier objects.
"""

from __future__ import annotations

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.common.dto.manager.rbac.request import (
    SearchEntitiesRequest,
)
from ai.backend.common.dto.manager.rbac.response import EntityDTO
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.permission.entity import EntityData
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
)
from ai.backend.manager.repositories.permission_controller.options import (
    EntityScopeConditions,
)

__all__ = ("EntityAdapter",)


class EntityAdapter(BaseFilterAdapter):
    """Adapter for converting entity requests to BatchQuerier objects."""

    def build_querier(
        self,
        scope_type: ScopeType,
        scope_id: str,
        entity_type: EntityType,
        request: SearchEntitiesRequest,
    ) -> BatchQuerier:
        """Build a BatchQuerier for entity search.

        Args:
            scope_type: The scope type to search within
            scope_id: The scope ID to search within
            entity_type: The type of entity to search
            request: The search request containing pagination info

        Returns:
            BatchQuerier with scope conditions and pagination settings
        """
        conditions = [
            EntityScopeConditions.by_scope_type(scope_type),
            EntityScopeConditions.by_scope_id(scope_id),
            EntityScopeConditions.by_entity_type(entity_type),
        ]
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return BatchQuerier(conditions=conditions, orders=[], pagination=pagination)

    def convert_to_dto(self, data: EntityData) -> EntityDTO:
        """Convert EntityData to DTO.

        Args:
            data: Entity data from action result

        Returns:
            EntityDTO for API response
        """
        return EntityDTO(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
        )
