"""
ImageV2 GQL resolver for Strawberry GraphQL.

This module provides GraphQL query fields for ImageV2.
"""

from __future__ import annotations

import uuid
from typing import Annotated
from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    ScopedSearchImagesInput,
    SearchImageAliasesInput,
)
from ai.backend.common.dto.manager.v2.image.types import ImageScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    ContainerRegistryScopeGQL,
    ImageSearchScopeGQL,
    ImageUsageGQL,
    ImageV2AliasConnectionGQL,
    ImageV2AliasEdgeGQL,
    ImageV2AliasFilterGQL,
    ImageV2AliasGQL,
    ImageV2AliasOrderByGQL,
    ImageV2ConnectionGQL,
    ImageV2EdgeGQL,
    ImageV2FilterGQL,
    ImageV2GQL,
    ImageV2OrderByGQL,
    ImageV2ScopeGQL,
)


# Query Fields
@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Query images with optional filtering, ordering, and pagination (admin only). Returns container images available in the system. Images are container specifications that define runtime environments for compute sessions. Use filters to narrow down results by status, name, or architecture. Supports both cursor-based and offset-based pagination.",
    )
)  # type: ignore[misc]
async def admin_images_v2(
    info: Info[StrawberryGQLContext],
    usage: Annotated[
        ImageUsageGQL | None,
        strawberry.argument(
            description=(
                f"Added in {NEXT_RELEASE_VERSION}. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; images the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: ImageV2FilterGQL | None = None,
    order_by: list[ImageV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageV2ConnectionGQL | None:
    check_admin_only()
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.image.admin_search_images_gql(
        AdminSearchImagesInput(
            usage=usage.to_pydantic() if usage else None,
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        ImageV2EdgeGQL(
            node=ImageV2GQL.from_pydantic(node),
            cursor=encode_cursor(node.id),
        )
        for node in payload.items
    ]
    page_info = strawberry.relay.PageInfo(
        has_next_page=payload.has_next_page,
        has_previous_page=payload.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    return ImageV2ConnectionGQL(count=payload.total_count, edges=edges, page_info=page_info)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the images the named scopes reach, combined with OR. "
            "Every scope is authorized before the read runs."
        ),
    ),
    name="scopedImagesV2",
)  # type: ignore[misc]
async def scoped_images_v2(
    info: Info[StrawberryGQLContext],
    scope: ImageSearchScopeGQL,
    usage: Annotated[
        ImageUsageGQL | None,
        strawberry.argument(
            description=(
                f"Added in {NEXT_RELEASE_VERSION}. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; images the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: ImageV2FilterGQL | None = None,
    order_by: list[ImageV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ImageV2ConnectionGQL | None:
    payload = await info.context.adapters.image.scoped_search(
        ScopedSearchImagesInput(
            scope=scope.to_pydantic(),
            usage=usage.to_pydantic() if usage else None,
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        ImageV2EdgeGQL(
            node=ImageV2GQL.from_pydantic(node),
            cursor=encode_cursor(node.id),
        )
        for node in payload.items
    ]
    page_info = strawberry.relay.PageInfo(
        has_next_page=payload.has_next_page,
        has_previous_page=payload.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    return ImageV2ConnectionGQL(count=payload.total_count, edges=edges, page_info=page_info)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Retrieve a specific image by its ID. Returns detailed information about the image including its identity, metadata, resource requirements, and permission settings.",
    )
)  # type: ignore[misc]
async def image_v2(id: ID, info: Info[StrawberryGQLContext]) -> ImageV2GQL | None:
    image_data = await info.context.data_loaders.image_loader.load(ImageID(UUID(id)))
    if image_data is None:
        return None
    return image_data


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Query images within a specific container registry with optional filtering, ordering, and pagination. Returns container images that belong to the specified registry. Use filters to narrow down results by status, name, or architecture. Supports both cursor-based and offset-based pagination.",
    )
)  # type: ignore[misc]
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
) -> ImageV2ConnectionGQL | None:
    payload = await info.context.adapters.image.scoped_search(
        ScopedSearchImagesInput(
            scope=ImageScope(container_registry=[UUIDScope(value=scope.registry_id)]),
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        ImageV2EdgeGQL(
            node=ImageV2GQL.from_pydantic(node),
            cursor=encode_cursor(node.id),
        )
        for node in payload.items
    ]
    page_info = strawberry.relay.PageInfo(
        has_next_page=payload.has_next_page,
        has_previous_page=payload.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    return ImageV2ConnectionGQL(count=payload.total_count, edges=edges, page_info=page_info)


# Image Alias Query Fields
@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Query image aliases with optional filtering, ordering, and pagination. Returns image aliases that provide alternative names for container images. Use filters to search by alias string. Supports both cursor-based and offset-based pagination.",
    )
)  # type: ignore[misc]
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
) -> ImageV2AliasConnectionGQL | None:
    check_admin_only()
    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None
    payload = await info.context.adapters.image.admin_search_image_aliases(
        AdminSearchImageAliasesInput(
            filter=pydantic_filter,
            order=pydantic_orders,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        ImageV2AliasEdgeGQL(
            node=ImageV2AliasGQL.from_pydantic(node),
            cursor=encode_cursor(node.id),
        )
        for node in payload.items
    ]
    page_info = strawberry.relay.PageInfo(
        has_next_page=payload.has_next_page,
        has_previous_page=payload.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    return ImageV2AliasConnectionGQL(count=payload.total_count, edges=edges, page_info=page_info)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Retrieve a specific image alias by its ID. Returns the alias information including the alias string.",
    )
)  # type: ignore[misc]
async def image_alias(id: ID, info: Info[StrawberryGQLContext]) -> ImageV2AliasGQL | None:
    alias_data = await info.context.data_loaders.image_alias_loader.load(
        ImageAliasID(uuid.UUID(id))
    )
    if alias_data is None:
        return None
    return alias_data


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Query image aliases within a specific image with optional filtering, ordering, and pagination. Returns image aliases that belong to the specified image. Supports both cursor-based and offset-based pagination.",
    )
)  # type: ignore[misc]
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
) -> ImageV2AliasConnectionGQL | None:
    payload = await info.context.adapters.image.scoped_search_aliases(
        ImageID(scope.image_id),
        SearchImageAliasesInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        ImageV2AliasEdgeGQL(
            node=ImageV2AliasGQL.from_pydantic(node),
            cursor=encode_cursor(node.id),
        )
        for node in payload.items
    ]
    page_info = strawberry.relay.PageInfo(
        has_next_page=payload.has_next_page,
        has_previous_page=payload.has_previous_page,
        start_cursor=edges[0].cursor if edges else None,
        end_cursor=edges[-1].cursor if edges else None,
    )
    return ImageV2AliasConnectionGQL(count=payload.total_count, edges=edges, page_info=page_info)
