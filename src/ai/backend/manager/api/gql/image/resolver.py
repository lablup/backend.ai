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
from ai.backend.manager.repositories.image.options import ImageConditions

from .fetcher import fetch_image, fetch_images
from .types import (
    ContainerRegistryScopeGQL,
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

    Query images within a specific container registry with optional filtering,
    ordering, and pagination.

    Returns container images that belong to the specified registry.
    Use filters to narrow down results by status, name, or architecture.
    Supports both cursor-based and offset-based pagination.
    """)
)
async def container_registry_images(
    info: Info[StrawberryGQLContext],
    scope: ContainerRegistryScopeGQL,
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
    # Add registry scope as base condition
    base_conditions = [ImageConditions.by_registry_id(scope.registry_id)]
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
        base_conditions=base_conditions,
    )


@strawberry.field(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Retrieve a specific image by its ID within a container registry scope.

    Returns detailed information about the image including its identity,
    metadata, resource requirements, and permission settings.
    Returns null if the image does not belong to the specified registry.
    """)
)
async def container_registry_image(
    info: Info[StrawberryGQLContext],
    scope: ContainerRegistryScopeGQL,
    id: ID,
) -> ImageV2GQL | None:
    image = await fetch_image(info, ImageID(UUID(id)))
    # Verify the image belongs to the specified registry
    if image is None or image.registry_id != scope.registry_id:
        return None
    return image
