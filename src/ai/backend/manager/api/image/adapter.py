"""
Filter adapter for image management REST API.
Converts request DTOs to repository query conditions and orders.
"""

from __future__ import annotations

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
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.image.types import ImageData, ImageDataWithDetails
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.image.options import ImageConditions, ImageOrders


class ImageAdapter(BaseFilterAdapter):
    """Adapter for converting image request DTOs to repository queries and response DTOs."""

    def convert_to_dto(self, data: ImageData) -> ImageDTO:
        """Convert internal ImageData to response ImageDTO."""
        return ImageDTO(
            id=data.id,
            name=data.name,
            registry=data.registry,
            registry_id=data.registry_id,
            project=data.project,
            tag=data.tag,
            architecture=data.architecture,
            size_bytes=data.size_bytes,
            type=str(data.type),
            status=str(data.status),
            labels=[ImageLabelEntryDTO(key=k, value=v) for k, v in data.labels.label_data.items()],
            tags=[ImageTagEntryDTO(key=t.key, value=t.value) for t in data.tags],
            resource_limits=[
                ImageResourceLimitDTO(key=rl.key, min=rl.min, max=rl.max)
                for rl in data.resource_limits
            ],
            accelerators=data.accelerators,
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
            registry_id=data.registry_id,
            project=data.project,
            tag=data.tag,
            architecture=data.architecture,
            size_bytes=data.size_bytes,
            type=str(data.type),
            status=str(data.status),
            labels=[ImageLabelEntryDTO(key=kv.key, value=kv.value) for kv in data.labels],
            tags=[ImageTagEntryDTO(key=kv.key, value=kv.value) for kv in data.tags],
            resource_limits=[
                ImageResourceLimitDTO(key=rl.key, min=rl.min, max=rl.max)
                for rl in data.resource_limits
            ],
            accelerators=",".join(data.supported_accelerators)
            if data.supported_accelerators
            else None,
            config_digest=data.digest or "",
            is_local=data.is_local,
            created_at=data.created_at,
        )

    def build_querier(self, request: SearchImagesRequest) -> BatchQuerier:
        """Convert search request to a BatchQuerier for the repository."""
        conditions = self._convert_filter(request.filter)
        orders = self._convert_order(request.order)
        pagination = self._build_pagination(request.offset, request.limit)
        return BatchQuerier(
            conditions=conditions,
            orders=orders,
            pagination=pagination,
        )

    def _convert_filter(self, filter_: ImageFilter | None) -> list[QueryCondition]:
        if filter_ is None:
            return []

        conditions: list[QueryCondition] = []

        if filter_.name is not None:
            condition = self.convert_string_filter(
                filter_.name,
                contains_factory=ImageConditions.by_name_contains,
                equals_factory=ImageConditions.by_name_equals,
                starts_with_factory=ImageConditions.by_name_starts_with,
                ends_with_factory=ImageConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter_.architecture is not None:
            condition = self.convert_string_filter(
                filter_.architecture,
                contains_factory=ImageConditions.by_architecture_contains,
                equals_factory=ImageConditions.by_architecture_equals,
                starts_with_factory=ImageConditions.by_architecture_starts_with,
                ends_with_factory=ImageConditions.by_architecture_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_order(self, orders: list[ImageOrder] | None) -> list[QueryOrder]:
        if not orders:
            return []

        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case ImageOrderField.NAME:
                    result.append(ImageOrders.name(ascending))
                case ImageOrderField.CREATED_AT:
                    result.append(ImageOrders.created_at(ascending))
        return result

    @staticmethod
    def _build_pagination(offset: int, limit: int) -> OffsetPagination:
        return OffsetPagination(limit=limit, offset=offset)
