"""VFolder GraphQL query resolvers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.vfolder.request import (
    ScopedSearchUserVFoldersInput,
    ScopedSearchVFoldersInput,
    SearchVFoldersInput,
)
from ai.backend.common.dto.manager.v2.vfolder.types import VFolderScope
from ai.backend.common.exception import UnreachableError
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.api.gql.vfolder_v2.types.filters import VFolderFilterGQL, VFolderOrderByGQL
from ai.backend.manager.api.gql.vfolder_v2.types.mount_policy import VFolderMountPoliciesPayloadGQL
from ai.backend.manager.api.gql.vfolder_v2.types.node import (
    VFolderConnection,
    VFolderEdge,
    VFolderGQL,
)
from ai.backend.manager.api.gql.vfolder_v2.types.scopes import VFolderScopeGQL, VFolderUsageGQL
from ai.backend.manager.api.gql.vfolder_v2.types.user_vfolder import (
    UserVFolderConnectionGQL,
    UserVFolderEdgeGQL,
    UserVFolderFilterGQL,
    UserVFolderGQL,
    UserVFolderOrderByGQL,
    UserVFolderScopeGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Search all virtual folders (superadmin only).",
    )
)
async def admin_vfolders_v2(
    info: Info[StrawberryGQLContext],
    usage: Annotated[
        VFolderUsageGQL | None,
        strawberry.argument(
            description=(
                "Added in 26.9.0. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; vfolders the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: VFolderFilterGQL | None = None,
    order_by: list[VFolderOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderConnection | None:
    """Search all virtual folders (superadmin only)."""
    check_admin_only()
    result = await info.context.adapters.vfolder.admin_search(
        SearchVFoldersInput(
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
        added_version="26.4.2",
        description="Get a single virtual folder by ID.",
    )
)
async def vfolder_v2(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
) -> VFolderGQL | None:
    """Get a single virtual folder by ID."""
    node = await info.context.adapters.vfolder.get(vfolder_id)
    return VFolderGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.9.0",
        description=(
            "Page through the virtual folders the named scopes reach, combined with OR. "
            "Every scope is authorized before the read runs."
        ),
    ),
    name="scopedVFoldersV2",
)
async def scoped_vfolders_v2(
    info: Info[StrawberryGQLContext],
    scope: VFolderScopeGQL,
    usage: Annotated[
        VFolderUsageGQL | None,
        strawberry.argument(
            description=(
                "Added in 26.9.0. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; vfolders the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: VFolderFilterGQL | None = None,
    order_by: list[VFolderOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderConnection | None:
    """Page through the virtual folders the named scopes reach."""
    result = await info.context.adapters.vfolder.scoped_search(
        ScopedSearchVFoldersInput(
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
        added_version="26.4.2",
        description="List virtual folders within a specific project.",
    )
)
async def project_vfolders(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
    usage: Annotated[
        VFolderUsageGQL | None,
        strawberry.argument(
            description=(
                "Added in 26.9.0. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; vfolders the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: VFolderFilterGQL | None = None,
    order_by: list[VFolderOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderConnection | None:
    """List virtual folders within a specific project."""
    result = await info.context.adapters.vfolder.project_search(
        project_id,
        SearchVFoldersInput(
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
        added_version="26.4.2",
        description="Search virtual folders accessible to the current user with pagination and filtering.",
    )
)
async def my_vfolders(
    info: Info[StrawberryGQLContext],
    usage: Annotated[
        VFolderUsageGQL | None,
        strawberry.argument(
            description=(
                "Added in 26.9.0. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; vfolders the caller cannot read "
                "are left out."
            )
        ),
    ] = None,
    filter: VFolderFilterGQL | None = None,
    order_by: list[VFolderOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderConnection | None:
    """Search virtual folders accessible to the current user."""
    me = current_user()
    if me is None:
        raise UnreachableError("User context is not available")
    result = await info.context.adapters.vfolder.scoped_search(
        ScopedSearchVFoldersInput(
            scope=VFolderScope(user=[UUIDScope(value=me.user_id)]),
            usage=usage.to_pydantic() if usage else None,
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


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the virtual folders the named scopes reach, each paired with the scope "
            "user. Every scope is authorized before the read runs."
        ),
    ),
    name="scopedUserVFolders",
)
async def scoped_user_vfolders(
    info: Info[StrawberryGQLContext],
    scope: UserVFolderScopeGQL,
    filter: UserVFolderFilterGQL | None = None,
    order_by: list[UserVFolderOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> UserVFolderConnectionGQL | None:
    """Page through the pairs of the scope user and the virtual folders the scopes reach."""
    result = await info.context.adapters.vfolder.scoped_search_user_vfolders(
        ScopedSearchUserVFoldersInput(
            scope=scope.to_pydantic(),
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
        UserVFolderEdgeGQL(
            node=UserVFolderGQL.from_pydantic(item), cursor=encode_cursor(item.vfolder_id)
        )
        for item in result.items
    ]
    return UserVFolderConnectionGQL(
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
        added_version="26.9.0",
        description="The mount levels set on a virtual folder, one row per user.",
    )
)
async def vfolder_mount_policies(
    info: Info[StrawberryGQLContext],
    vfolder_id: UUID,
) -> VFolderMountPoliciesPayloadGQL | None:
    payload = await info.context.adapters.vfolder.list_mount_policies(vfolder_id)
    return VFolderMountPoliciesPayloadGQL.from_pydantic(payload)
