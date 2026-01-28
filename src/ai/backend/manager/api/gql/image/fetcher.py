"""
ImageV2 GQL fetcher functions for Strawberry GraphQL.

This module provides data fetching logic for ImageV2 queries.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.services.image.actions.get_images_by_ids import GetImagesByIdsAction
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction

from .types import (
    ImageConnectionV2GQL,
    ImageEdgeGQL,
    ImageFilterGQL,
    ImageOrderByGQL,
    ImageV2GQL,
)


@lru_cache(maxsize=1)
def _get_image_pagination_spec() -> PaginationSpec:
    """Get pagination spec for Image queries."""
    return PaginationSpec(
        forward_order=ImageRow.id.asc(),
        backward_order=ImageRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ImageRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ImageRow.id < cursor_value,
    )


async def fetch_images(
    info: Info[StrawberryGQLContext],
    filter: Optional[ImageFilterGQL] = None,
    order_by: Optional[list[ImageOrderByGQL]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    base_conditions: Optional[list[QueryCondition]] = None,
) -> ImageConnectionV2GQL:
    """Fetch images with optional filtering, ordering, and pagination.

    Uses a two-step approach:
    1. Search for image IDs using batch querier
    2. Fetch detailed data using get_images_by_ids

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend
    """
    # Build querier using adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_image_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    # Step 1: Get image IDs using search action
    search_result = await info.context.processors.image.search_images.wait_for_complete(
        SearchImagesAction(querier=querier)
    )

    if not search_result.data:
        # No images found, return empty connection
        page_info = strawberry.relay.PageInfo(
            has_next_page=search_result.has_next_page,
            has_previous_page=search_result.has_previous_page,
            start_cursor=None,
            end_cursor=None,
        )
        return ImageConnectionV2GQL(
            count=search_result.total_count,
            edges=[],
            page_info=page_info,
        )

    # Step 2: Fetch detailed data using get_images_by_ids
    # Cast ImageID (NewType of UUID) to UUID for the action
    image_ids: list[UUID] = [UUID(str(img.id)) for img in search_result.data]
    detailed_result = await info.context.processors.image.get_images_by_ids.wait_for_complete(
        GetImagesByIdsAction(
            image_ids=image_ids,
            user_role=UserRole.SUPERADMIN,  # TODO: Get from context
            image_status=None,  # Already filtered in search
        )
    )

    # Build a map of image_id -> detailed data for ordering
    detailed_map = {img.image.id: img for img in detailed_result.images}

    # Build GraphQL connection response, preserving search order
    edges = []
    for simple_image in search_result.data:
        image_id = simple_image.id
        detailed_image = detailed_map.get(image_id)
        if detailed_image:
            image = ImageV2GQL.from_data(detailed_image.image)
            cursor = encode_cursor(detailed_image.image.id)
            edges.append(ImageEdgeGQL(node=image, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=search_result.has_next_page,
        has_previous_page=search_result.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ImageConnectionV2GQL(
        count=search_result.total_count,
        edges=edges,
        page_info=page_info,
    )


async def fetch_image_by_id(
    info: Info[StrawberryGQLContext],
    image_id: UUID,
) -> Optional[ImageV2GQL]:
    """Fetch a single image by ID.

    Args:
        info: GraphQL context info
        image_id: The UUID of the image to fetch

    Returns:
        ImageV2GQL if found, None otherwise
    """
    action_result = await info.context.processors.image.get_images_by_ids.wait_for_complete(
        GetImagesByIdsAction(
            image_ids=[image_id],
            user_role=UserRole.SUPERADMIN,  # TODO: Get from context
            image_status=[ImageStatus.ALIVE],
        )
    )

    if not action_result.images:
        return None

    return ImageV2GQL.from_data(action_result.images[0].image)
