"""
Filter adapter for image management REST API.
Converts request DTOs to repository query conditions and orders.
"""

from __future__ import annotations

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.dto.manager.image import (
    ImageFilter,
    ImageOrder,
    SearchImagesRequest,
)
from ai.backend.common.dto.manager.image.response import (
    ImageDTO,
    ImageLabelEntryDTO,
    ImageResourceLimitDTO,
    ImageTagEntryDTO,
)
from ai.backend.common.dto.manager.image.types import ImageOrderField, OrderDirection
from ai.backend.manager.data.image.types import ImageData, ImageDataWithDetails
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.image.searchable_fields import ImageSearchableFields
from ai.backend.manager.models.image.searchers import ImageSearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter


class ImageAdapter(BaseFilterAdapter):
    """Adapter for converting image request DTOs to repository queries and response DTOs."""

    def convert_to_dto(self, data: ImageData) -> ImageDTO:
        """Convert internal ImageData to response ImageDTO."""
        return ImageDTO(
            id=data.id,
            name=data.name,
            registry=data.registry,
            registry_id=ArtifactRegistryID(data.registry_id),
            project=data.project,
            tag=data.tag,
            architecture=data.architecture,
            size_bytes=data.size_bytes,
            type=str(data.type),
            status=str(data.status),
            labels=[ImageLabelEntryDTO(key=k, value=v) for k, v in data.labels.label_data.items()],
            tags=[ImageTagEntryDTO(key=t.key, value=t.value) for t in data.tags],
            resource_limits=[
                ImageResourceLimitDTO.model_validate({"key": rl.key, **rl.value_to_dict()})
                for rl in data.resource_limits
            ],
            accelerators=data.accelerators if data.accelerators else "*",
            config_digest=data.config_digest,
            is_local=data.is_local,
            created_at=data.created_at,
        )

    def convert_detailed_to_dto(self, data: ImageDataWithDetails) -> ImageDTO:
        """Convert internal ImageDataWithDetails to response ImageDTO."""
        return ImageDTO(
            id=data.id,
            name=data.name,
            registry=data.registry,
            registry_id=ArtifactRegistryID(data.registry_id),
            project=data.project,
            tag=data.tag,
            architecture=data.architecture,
            size_bytes=data.size_bytes,
            type=str(data.type),
            status=str(data.status),
            labels=[ImageLabelEntryDTO(key=kv.key, value=kv.value) for kv in data.labels],
            tags=[ImageTagEntryDTO(key=kv.key, value=kv.value) for kv in data.tags],
            resource_limits=[
                ImageResourceLimitDTO.model_validate({"key": rl.key, **rl.value_to_dict()})
                for rl in data.resource_limits
            ],
            accelerators=",".join(data.supported_accelerators)
            if data.supported_accelerators
            else None,
            config_digest=data.digest or "",
            is_local=data.is_local,
            created_at=data.created_at,
        )

    def build_searcher(self, request: SearchImagesRequest) -> ImageSearcher:
        """Convert a search request to the searcher the read runs."""
        return ImageSearcher(
            pagination=self._build_pagination(request.offset, request.limit),
            conditions=self._convert_filter(request.filter),
            orders=self._convert_order(request.order),
        )

    def _convert_filter(self, filter_: ImageFilter | None) -> list[QueryCondition]:
        if filter_ is None:
            return []
        fields = ImageSearchableFields.own
        return [
            *self.apply_string_filter(filter_.name, fields.name.filter),
            *self.apply_string_filter(filter_.architecture, fields.architecture.filter),
        ]

    def _convert_order(self, orders: list[ImageOrder] | None) -> list[QueryOrder]:
        if not orders:
            return []
        fields = ImageSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case ImageOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
                case ImageOrderField.CREATED_AT:
                    result.append(fields.created_at.order.apply(ascending))
                case ImageOrderField.LAST_USED:
                    result.append(fields.last_used_at.order.apply(ascending))
        return result

    @staticmethod
    def _build_pagination(offset: int, limit: int) -> OffsetPagination:
        return OffsetPagination(limit=limit, offset=offset)
