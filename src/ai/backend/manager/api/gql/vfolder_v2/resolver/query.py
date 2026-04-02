"""VFolder GraphQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder_v2.types import (
    VFolderConnection,
    VFolderFilterGQL,
    VFolderGQL,
    VFolderOrderByGQL,
)
from ai.backend.manager.api.gql.vfolder_v2.types.node import VFolderEdge


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List virtual folders within a specific project.",
    )
)  # type: ignore[misc]
async def project_vfolders(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    filter: VFolderFilterGQL | None = None,
    order_by: list[VFolderOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderConnection:
    """List virtual folders within a specific project."""
    result = await info.context.adapters.vfolder.project_search(
        project_id,
        SearchVFoldersInput(
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
    nodes = [VFolderGQL.from_pydantic(item) for item in result.items]
    edges = [VFolderEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return VFolderConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Search virtual folders accessible to the current user with pagination and filtering.",
    )
)  # type: ignore[misc]
async def my_vfolders(
    info: Info[StrawberryGQLContext],
    filter: VFolderFilterGQL | None = None,
    order_by: list[VFolderOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderConnection:
    """Search virtual folders accessible to the current user."""
    result = await info.context.adapters.vfolder.my_search(
        SearchVFoldersInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [VFolderGQL.from_pydantic(item) for item in result.items]
    edges = [VFolderEdge(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return VFolderConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
