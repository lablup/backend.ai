"""
ImageV2 GQL resolver for Strawberry GraphQL.

This module provides GraphQL query fields for ImageV2.
"""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only, dedent_strip

from .fetcher import fetch_image, fetch_images
from .types import (
    ImageConnectionV2GQL,
    ImageFilterGQL,
    ImageOrderByGQL,
    ImageStatusGQL,
    ImageV2GQL,
)


# Query Fields
@strawberry.field(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Query images with optional filtering, ordering, and pagination (admin only).

    Returns container images available in the system. Images are container
    specifications that define runtime environments for compute sessions.

    Use filters to narrow down results by status, name, or architecture.
    Supports both cursor-based and offset-based pagination.
    """)
)
async def admin_images(
    info: Info[StrawberryGQLContext],
    filter: ImageFilterGQL | None = None,
    order_by: list[ImageOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageConnectionV2GQL:
    check_admin_only()
    # Default filter to ALIVE status if not specified
    if filter is None:
        filter = ImageFilterGQL(status=[ImageStatusGQL.ALIVE])
    return await fetch_images(
        info,
        filter,
        order_by,
        before,
        after,
        first,
        last,
        limit,
        offset,
    )


@strawberry.field(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Retrieve a specific image by its ID (admin only).

    Returns detailed information about the image including its identity,
    metadata, resource requirements, and permission settings.
    """)
)
async def admin_image(id: ID, info: Info[StrawberryGQLContext]) -> ImageV2GQL | None:
    check_admin_only()
    return await fetch_image(info, ImageID(UUID(id)))


@strawberry.field(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Query images with optional filtering, ordering, and pagination.

    Returns container images available in the system. Images are container
    specifications that define runtime environments for compute sessions.

    Use filters to narrow down results by status, name, or architecture.
    Supports both cursor-based and offset-based pagination.
    """),
    deprecation_reason=(
        "Use admin_images instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def images_v2(
    info: Info[StrawberryGQLContext],
    filter: ImageFilterGQL | None = None,
    order_by: list[ImageOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageConnectionV2GQL:
    # Default filter to ALIVE status if not specified
    if filter is None:
        filter = ImageFilterGQL(status=[ImageStatusGQL.ALIVE])
    return await fetch_images(
        info,
        filter,
        order_by,
        before,
        after,
        first,
        last,
        limit,
        offset,
    )


@strawberry.field(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Retrieve a specific image by its ID.

    Returns detailed information about the image including its identity,
    metadata, resource requirements, and permission settings.
    """),
    deprecation_reason=(
        "Use admin_image instead. "
        "This API will be removed after v26.3.0. See BEP-1041 for migration guide."
    ),
)
async def image_v2(id: ID, info: Info[StrawberryGQLContext]) -> ImageV2GQL | None:
    return await fetch_image(info, ImageID(UUID(id)))
