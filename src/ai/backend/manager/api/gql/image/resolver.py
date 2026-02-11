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
from ai.backend.manager.repositories.image.options import ImageAliasConditions, ImageConditions

from .fetcher import fetch_image, fetch_image_alias, fetch_image_aliases, fetch_images
from .types import (
    ContainerRegistryScopeGQL,
    ImageV2AliasConnectionGQL,
    ImageV2AliasFilterGQL,
    ImageV2AliasGQL,
    ImageV2AliasOrderByGQL,
    ImageV2ConnectionGQL,
    ImageV2FilterGQL,
    ImageV2GQL,
    ImageV2OrderByGQL,
    ImageV2ScopeGQL,
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
    filter: ImageV2FilterGQL | None = None,
    order_by: list[ImageV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageV2ConnectionGQL:
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
    filter: ImageV2FilterGQL | None = None,
    order_by: list[ImageV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageV2ConnectionGQL:
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
    filter: ImageV2AliasFilterGQL | None = None,
    order_by: list[ImageV2AliasOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageV2AliasConnectionGQL:
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
async def image_alias(id: ID, info: Info[StrawberryGQLContext]) -> ImageV2AliasGQL | None:
    return await fetch_image_alias(info, UUID(id))


@strawberry.field(  # type: ignore[misc]
    description=dedent_strip("""
    Added in 26.2.0.

    Query image aliases within a specific image with optional filtering,
    ordering, and pagination.

    Returns image aliases that belong to the specified image.
    Supports both cursor-based and offset-based pagination.
    """)
)
async def image_scoped_aliases(
    info: Info[StrawberryGQLContext],
    scope: ImageV2ScopeGQL,
    filter: ImageV2AliasFilterGQL | None = None,
    order_by: list[ImageV2AliasOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageV2AliasConnectionGQL:
    # Add image scope as base condition
    base_conditions = [ImageAliasConditions.by_image_ids([ImageID(scope.image_id)])]
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
        base_conditions=base_conditions,
    )
