"""
ImageV2 GQL fetcher functions for Strawberry GraphQL.

This module provides data fetching logic for ImageV2 queries.
"""

from __future__ import annotations

import uuid
from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.services.image.actions.search_aliases import SearchAliasesAction
from ai.backend.manager.services.image.actions.search_images import SearchImagesAction

from .types import (
    ImageAliasConnectionGQL,
    ImageAliasEdgeGQL,
    ImageAliasFilterGQL,
    ImageAliasGQL,
    ImageAliasOrderByGQL,
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
        tiebreaker_order=ImageRow.id.asc(),
    )


async def fetch_images(
    info: Info[StrawberryGQLContext],
    filter: ImageFilterGQL | None = None,
    order_by: list[ImageOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> ImageConnectionV2GQL:
    """Fetch images with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend
    """
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

    action_result = await info.context.processors.image.search_images.wait_for_complete(
        SearchImagesAction(querier=querier)
    )

    edges = []
    for image_data in action_result.data:
        image = ImageV2GQL.from_data(image_data)
        cursor = encode_cursor(image_data.id)
        edges.append(ImageEdgeGQL(node=image, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=action_result.has_next_page,
        has_previous_page=action_result.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ImageConnectionV2GQL(
        count=action_result.total_count,
        edges=edges,
        page_info=page_info,
    )


async def fetch_image(
    info: Info[StrawberryGQLContext],
    image_id: ImageID,
) -> ImageV2GQL | None:
    """Fetch a single image by ID using dataloader.

    Args:
        info: GraphQL context info
        image_id: The ImageID of the image to fetch

    Returns:
        ImageV2GQL if found, None otherwise
    """
    image_data = await info.context.data_loaders.image_loader.load(image_id)
    if image_data is None:
        return None
    return ImageV2GQL.from_data(image_data)


# =============================================================================
# Image Alias Fetchers
# =============================================================================


async def fetch_image_alias(
    info: Info[StrawberryGQLContext],
    alias_id: uuid.UUID,
) -> ImageAliasGQL | None:
    """Fetch a single image alias by ID using dataloader.

    Args:
        info: GraphQL context info
        alias_id: The UUID of the alias to fetch

    Returns:
        ImageAliasGQL if found, None otherwise
    """
    alias_data = await info.context.data_loaders.image_alias_loader.load(alias_id)
    if alias_data is None:
        return None
    return ImageAliasGQL.from_data(alias_data)


@lru_cache(maxsize=1)
def _get_image_alias_pagination_spec() -> PaginationSpec:
    """Get pagination spec for ImageAlias queries."""
    return PaginationSpec(
        forward_order=ImageAliasRow.id.asc(),
        backward_order=ImageAliasRow.id.desc(),
        forward_condition_factory=lambda cursor_value: lambda: ImageAliasRow.id > cursor_value,
        backward_condition_factory=lambda cursor_value: lambda: ImageAliasRow.id < cursor_value,
        tiebreaker_order=ImageAliasRow.id.asc(),
    )


async def fetch_image_aliases(
    info: Info[StrawberryGQLContext],
    filter: ImageAliasFilterGQL | None = None,
    order_by: list[ImageAliasOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    base_conditions: list[QueryCondition] | None = None,
) -> ImageAliasConnectionGQL:
    """Fetch image aliases with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend
    """
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        _get_image_alias_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await info.context.processors.image.search_aliases.wait_for_complete(
        SearchAliasesAction(querier=querier)
    )

    edges = []
    for alias_data in action_result.data:
        alias_node = ImageAliasGQL.from_data(alias_data)
        cursor = encode_cursor(alias_data.id)
        edges.append(ImageAliasEdgeGQL(node=alias_node, cursor=cursor))

    page_info = strawberry.relay.PageInfo(
        has_next_page=action_result.has_next_page,
        has_previous_page=action_result.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )

    return ImageAliasConnectionGQL(
        count=action_result.total_count,
        edges=edges,
        page_info=page_info,
    )
