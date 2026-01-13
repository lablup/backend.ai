"""
Adapter for Entity API requests.
Handles conversion of request DTOs to BatchQuerier objects.
"""

from __future__ import annotations

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

__all__ = ("EntityAdapter",)


class EntityAdapter(BaseFilterAdapter):
    """Adapter for converting entity requests to BatchQuerier objects."""

    def build_querier(self, request: SearchEntitiesRequest) -> BatchQuerier:
        """Build a BatchQuerier for entity search.

        Args:
            request: The search request containing pagination info

        Returns:
            BatchQuerier with pagination settings
        """
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)
        return BatchQuerier(conditions=[], orders=[], pagination=pagination)

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
