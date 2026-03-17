"""Image domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImagesInput,
    ImageFilter,
    ImageOrder,
)
from ai.backend.common.dto.manager.v2.image.response import AdminSearchImagesPayload, ImageNode
from ai.backend.common.dto.manager.v2.image.types import (
    ImageLabelInfo,
    ImageResourceLimitInfo,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
    OrderDirection,
)
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.conditions import ImageConditions
from ai.backend.manager.models.image.orders import ImageOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 50


class ImageAdapter(BaseAdapter):
    """Adapter for image domain operations."""

    async def admin_search(self, input: AdminSearchImagesInput) -> AdminSearchImagesPayload:
        """Search images with admin scope.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = await self._processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=querier)
        )

        return AdminSearchImagesPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchImagesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: ImageFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ImageConditions.by_name_contains,
                equals_factory=ImageConditions.by_name_equals,
                starts_with_factory=ImageConditions.by_name_starts_with,
                ends_with_factory=ImageConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.architecture is not None:
            condition = self.convert_string_filter(
                filter.architecture,
                contains_factory=ImageConditions.by_architecture_contains,
                equals_factory=ImageConditions.by_architecture_equals,
                starts_with_factory=ImageConditions.by_architecture_starts_with,
                ends_with_factory=ImageConditions.by_architecture_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    @staticmethod
    def _convert_orders(orders: list[ImageOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field.value:
                case "name":
                    result.append(ImageOrders.name(ascending))
                case "created_at":
                    result.append(ImageOrders.created_at(ascending))
                case "last_used":
                    result.append(ImageOrders.last_used(ascending))
        return result

    @staticmethod
    def _build_pagination(input: AdminSearchImagesInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _convert_max(value: Decimal | str) -> Decimal | None:
        if isinstance(value, str):
            value = Decimal(value)
        return None if value.is_infinite() else value

    def _data_to_dto(self, data: ImageData) -> ImageNode:
        """Convert data layer type to Pydantic DTO."""
        return ImageNode(
            id=data.id,
            name=str(data.name),
            registry=data.registry,
            registry_id=data.registry_id,
            project=data.project,
            tag=data.tag,
            architecture=data.architecture,
            size_bytes=data.size_bytes,
            type=ImageTypeEnum(data.type.value),
            status=ImageStatusType(data.status.value),
            labels=[ImageLabelInfo(key=k, value=v) for k, v in data.labels.label_data.items()],
            tags=[ImageTagInfo(key=e.key, value=e.value) for e in data.tags],
            resource_limits=[
                ImageResourceLimitInfo(
                    key=rl.key,
                    min=rl.min,
                    max=self._convert_max(rl.max),
                )
                for rl in data.resource_limits
            ],
            accelerators=data.accelerators,
            config_digest=data.config_digest,
            is_local=data.is_local,
            created_at=data.created_at,
        )
