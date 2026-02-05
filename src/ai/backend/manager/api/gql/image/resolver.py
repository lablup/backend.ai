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

from .fetcher import fetch_image, fetch_image_alias, fetch_image_aliases, fetch_images
from .types import (
    ContainerRegistryScopeGQL,
    ImageAliasConnectionGQL,
    ImageAliasFilterGQL,
    ImageAliasGQL,
    ImageAliasOrderByGQL,
    ImageConnectionV2GQL,
    ImageFilterGQL,
    ImageOrderByGQL,
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
async def admin_images_v2(
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
    """)
)
async def image_v2(id: ID, info: Info[StrawberryGQLContext]) -> ImageV2GQL | None:
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
async def container_registry_images_v2(
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


# Image Alias Query Fields
@strawberry.field(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Query image aliases with optional filtering, ordering, and pagination.

    Returns image aliases that provide alternative names for container images.
    Use filters to search by alias string.
    Supports both cursor-based and offset-based pagination.
    """)
)
async def admin_image_aliases(
    info: Info[StrawberryGQLContext],
    filter: ImageAliasFilterGQL | None = None,
    order_by: list[ImageAliasOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageAliasConnectionGQL:
    check_admin_only()
    return await fetch_image_aliases(
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

    Retrieve a specific image alias by its ID.

    Returns the alias information including the alias string.
    """)
)
async def admin_image_alias(id: ID, info: Info[StrawberryGQLContext]) -> ImageAliasGQL | None:
    check_admin_only()
    return await fetch_image_alias(info, UUID(id))
