"""Image domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from decimal import Decimal
from functools import lru_cache

from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    ImageAliasFilterInputDTO,
    ImageAliasOrderByInputDTO,
    ImageFilterInputDTO,
    ImageOrderByInputDTO,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
    ImageAliasNode,
    ImageIdentityInfoDTO,
    ImageMetadataInfoDTO,
    ImageNode,
    ImageRequirementsInfoDTO,
)
from ai.backend.common.dto.manager.v2.image.types import (
    ImageLabelInfo,
    ImageResourceLimitGQLInfo,
    ImageResourceLimitInfo,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
    OrderDirection,
)
from ai.backend.common.types import ImageID
from ai.backend.manager.data.image.types import ImageAliasData, ImageData, ImageStatus
from ai.backend.manager.models.image.conditions import (
    ImageAliasConditions,
    ImageConditions,
)
from ai.backend.manager.models.image.orders import ImageAliasOrders, ImageOrders
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.image.actions.search_aliases import SearchAliasesAction
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction

from .base import BaseAdapter
from .pagination import PaginationSpec

DEFAULT_PAGINATION_LIMIT = 50


@lru_cache(maxsize=1)
def _get_image_pagination_spec() -> PaginationSpec:
    """Get pagination spec for Image queries."""
    return PaginationSpec(
        forward_order=ImageRow.id.asc(),
        backward_order=ImageRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ImageRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ImageRow.id < cursor_value,
        tiebreaker_order=ImageRow.id.asc(),
    )


@lru_cache(maxsize=1)
def _get_alias_pagination_spec() -> PaginationSpec:
    """Get pagination spec for ImageAlias queries."""
    return PaginationSpec(
        forward_order=ImageAliasRow.id.asc(),
        backward_order=ImageAliasRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ImageAliasRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ImageAliasRow.id < cursor_value,
        tiebreaker_order=ImageAliasRow.id.asc(),
    )


class ImageAdapter(BaseAdapter):
    """Adapter for image domain operations."""

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(self, image_ids: Sequence[ImageID]) -> list[ImageNode | None]:
        """Batch load images by ID for DataLoader use.

        Returns ImageNode DTOs in the same order as the input image_ids list.
        """
        if not image_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ImageConditions.by_ids(image_ids)],
        )
        action_result = await self._processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=querier)
        )
        image_map: dict[ImageID, ImageNode] = {
            ImageID(item.id): self._data_to_dto(item) for item in action_result.data
        }
        return [image_map.get(image_id) for image_id in image_ids]

    async def batch_load_aliases_by_ids(
        self, alias_ids: Sequence[uuid.UUID]
    ) -> list[ImageAliasNode | None]:
        """Batch load image aliases by alias ID for DataLoader use.

        Returns ImageAliasNode DTOs in the same order as the input alias_ids list.
        """
        if not alias_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ImageAliasConditions.by_ids(alias_ids)],
        )
        action_result = await self._processors.image.search_aliases.wait_for_complete(
            SearchAliasesAction(querier=querier)
        )
        alias_map: dict[uuid.UUID, ImageAliasNode] = {
            item.id: self._alias_data_to_dto(item) for item in action_result.data
        }
        return [alias_map.get(alias_id) for alias_id in alias_ids]

    # ------------------------------------------------------------------ search

    async def admin_search(self, input: AdminSearchImagesInput) -> AdminSearchImagesPayload:
        """Search images with admin scope using offset pagination."""
        querier = self._build_offset_querier(input)

        action_result = await self._processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=querier)
        )

        return AdminSearchImagesPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_images_gql(
        self,
        input: AdminSearchImagesInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> AdminSearchImagesPayload:
        """Search images with cursor or offset pagination for GQL resolvers."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_image_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=list(base_conditions) if base_conditions else None,
        )

        action_result = await self._processors.image.search_images.wait_for_complete(
            SearchImagesAction(querier=querier)
        )

        return AdminSearchImagesPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_search_image_aliases(
        self,
        input: AdminSearchImageAliasesInput,
        base_conditions: Sequence[QueryCondition] | None = None,
    ) -> AdminSearchImageAliasesPayload:
        """Search image aliases with cursor or offset pagination for GQL resolvers."""
        conditions = self._convert_alias_filter(input.filter) if input.filter else []
        orders = self._convert_alias_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_get_alias_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
            base_conditions=list(base_conditions) if base_conditions else None,
        )

        action_result = await self._processors.image.search_aliases.wait_for_complete(
            SearchAliasesAction(querier=querier)
        )

        return AdminSearchImageAliasesPayload(
            items=[self._alias_data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _build_offset_querier(self, input: AdminSearchImagesInput) -> BatchQuerier:
        """Build a BatchQuerier with offset pagination from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(
        self,
        filter: ImageFilterInputDTO,
        base_conditions: list[QueryCondition] | None = None,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = list(base_conditions) if base_conditions else []

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

        if filter.status is not None:
            st = filter.status
            if st.equals is not None:
                conditions.append(ImageConditions.by_status_equals(ImageStatus(st.equals.value)))
            if st.in_ is not None:
                conditions.append(
                    ImageConditions.by_statuses([ImageStatus(s.value) for s in st.in_])
                )
            if st.not_equals is not None:
                conditions.append(
                    ImageConditions.by_status_not_equals(ImageStatus(st.not_equals.value))
                )
            if st.not_in is not None:
                conditions.append(
                    ImageConditions.by_status_not_in([ImageStatus(s.value) for s in st.not_in])
                )

        if filter.registry_id is not None:
            rid = filter.registry_id
            if rid.equals is not None:
                conditions.append(ImageConditions.by_registry_id(rid.equals))
            elif rid.in_ is not None:
                # Multiple registry IDs: combine with OR
                sub: list[QueryCondition] = [ImageConditions.by_registry_id(r) for r in rid.in_]
                conditions.append(combine_conditions_or(sub))

        if filter.alias is not None:
            alias_f = filter.alias
            if alias_f.alias is not None:
                condition = self.convert_string_filter(
                    alias_f.alias,
                    contains_factory=ImageConditions.by_alias_contains,
                    equals_factory=ImageConditions.by_alias_equals,
                    starts_with_factory=ImageConditions.by_alias_starts_with,
                    ends_with_factory=ImageConditions.by_alias_ends_with,
                )
                if condition is not None:
                    conditions.append(condition)

        if filter.last_used is not None:
            lu = filter.last_used
            if lu.before is not None:
                conditions.append(ImageConditions.by_last_used_before(lu.before))
            if lu.after is not None:
                conditions.append(ImageConditions.by_last_used_after(lu.after))

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))

        if filter.OR:
            or_sub: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_sub.extend(self._convert_filter(sub_filter))
            if or_sub:
                conditions.append(combine_conditions_or(or_sub))

        if filter.NOT:
            not_sub: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_sub.extend(self._convert_filter(sub_filter))
            if not_sub:
                conditions.append(negate_conditions(not_sub))

        return conditions

    def _convert_alias_filter(
        self,
        filter: ImageAliasFilterInputDTO,
    ) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.alias is not None:
            condition = self.convert_string_filter(
                filter.alias,
                contains_factory=ImageAliasConditions.by_alias_contains,
                equals_factory=ImageAliasConditions.by_alias_equals,
                starts_with_factory=ImageAliasConditions.by_alias_starts_with,
                ends_with_factory=ImageAliasConditions.by_alias_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.image_id is not None:
            iid = filter.image_id
            if iid.equals is not None:
                conditions.append(ImageAliasConditions.by_image_ids([ImageID(iid.equals)]))
            elif iid.in_ is not None:
                conditions.append(ImageAliasConditions.by_image_ids([ImageID(i) for i in iid.in_]))

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_alias_filter(sub_filter))

        if filter.OR:
            or_sub: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_sub.extend(self._convert_alias_filter(sub_filter))
            if or_sub:
                conditions.append(combine_conditions_or(or_sub))

        if filter.NOT:
            not_sub: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_sub.extend(self._convert_alias_filter(sub_filter))
            if not_sub:
                conditions.append(negate_conditions(not_sub))

        return conditions

    @staticmethod
    def _convert_orders(orders: list[ImageOrderByInputDTO]) -> list[QueryOrder]:
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
    def _convert_alias_orders(orders: list[ImageAliasOrderByInputDTO]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field:
                case "alias":
                    result.append(ImageAliasOrders.alias(ascending))
        return result

    @staticmethod
    def _convert_max(value: Decimal | str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return None if value.is_infinite() else str(value)
        return str(value)

    def _data_to_dto(self, data: ImageData) -> ImageNode:
        """Convert data layer type to Pydantic DTO."""
        status = ImageStatusType(data.status.value)
        labels = [ImageLabelInfo(key=k, value=v) for k, v in data.labels.label_data.items()]
        tags = [ImageTagInfo(key=e.key, value=e.value) for e in data.tags]
        resource_limits_flat = [
            ImageResourceLimitInfo(
                key=rl.key,
                min=str(rl.min),
                max=self._convert_max(rl.max),
            )
            for rl in data.resource_limits
        ]
        accelerators = data.accelerators
        accelerator_list = (
            [a.strip() for a in accelerators.split(",") if a.strip()] if accelerators else []
        )
        resource_limits_gql = [
            ImageResourceLimitGQLInfo(
                key=rl.key,
                min=str(rl.min),
                max=str(rl.max) if rl.max is not None else "Infinity",
            )
            for rl in data.resource_limits
        ]
        return ImageNode(
            id=data.id,
            name=str(data.name),
            image=data.image,
            registry=data.registry,
            registry_id=data.registry_id,
            project=data.project,
            tag=data.tag,
            architecture=data.architecture,
            size_bytes=data.size_bytes,
            type=ImageTypeEnum(data.type.value),
            status=status,
            labels=labels,
            tags=tags,
            resource_limits=resource_limits_flat,
            accelerators=accelerators,
            config_digest=data.config_digest,
            is_local=data.is_local,
            created_at=data.created_at,
            last_used_at=data.last_used_at,
            identity=ImageIdentityInfoDTO(
                canonical_name=str(data.name),
                namespace=data.image,
                architecture=data.architecture,
            ),
            metadata=ImageMetadataInfoDTO(
                digest=data.config_digest,
                size_bytes=data.size_bytes,
                created_at=data.created_at,
                last_used_at=data.last_used_at,
                tags=tags,
                labels=labels,
                status=status,
            ),
            requirements=ImageRequirementsInfoDTO(
                supported_accelerators=accelerator_list,
                resource_limits=resource_limits_gql,
            ),
        )

    @staticmethod
    def _alias_data_to_dto(data: ImageAliasData) -> ImageAliasNode:
        """Convert alias data layer type to Pydantic DTO."""
        return ImageAliasNode(
            id=data.id,
            alias=data.alias,
        )

    def build_querier(self, input: AdminSearchImagesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO (offset pagination)."""
        return self._build_offset_querier(input)

    def _build_pagination(self, input: AdminSearchImagesInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    def _convert_orders_legacy(self, orders: list[ImageOrderByInputDTO]) -> list[QueryOrder]:
        return self._convert_orders(orders)
