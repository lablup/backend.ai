"""VFolder auto-mount GraphQL query and mutation resolvers."""

from __future__ import annotations

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    ScopedSearchVFolderAutoMountsInput,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    SearchVFolderAutoMountsPayload,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.vfolder_auto_mount.types import (
    CreateVFolderAutoMountInputGQL,
    CreateVFolderAutoMountPayloadGQL,
    DeleteVFolderAutoMountInputGQL,
    DeleteVFolderAutoMountPayloadGQL,
    UpdateVFolderAutoMountInputGQL,
    UpdateVFolderAutoMountPayloadGQL,
    VFolderAutoMountConnectionGQL,
    VFolderAutoMountEdgeGQL,
    VFolderAutoMountFilterGQL,
    VFolderAutoMountGQL,
    VFolderAutoMountOrderByGQL,
    VFolderAutoMountScopeGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the vfolder auto-mounts of the named projects and users, combined "
            "with OR. "
            "Every project is authorized before the read runs. Auto-mounts marked deleted "
            "are left out unless the filter names `deletedAt`."
        ),
    )
)  # type: ignore[misc]
async def scoped_vfolder_auto_mounts(
    info: Info[StrawberryGQLContext],
    scope: VFolderAutoMountScopeGQL,
    filter: VFolderAutoMountFilterGQL | None = None,
    order_by: list[VFolderAutoMountOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> VFolderAutoMountConnectionGQL | None:
    payload = await info.context.adapters.vfolder_auto_mount.scoped_search(
        ScopedSearchVFolderAutoMountsInput(
            scope=scope.to_pydantic(),
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
    return build_vfolder_auto_mount_connection(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Auto-mount a vfolder into every session created in a project or by a user. The "
            "vfolder must belong to the project, or be owned by the user, and the caller needs "
            "the auto-mount create permission on that project or user."
        ),
    )
)
async def create_vfolder_auto_mount(
    info: Info[StrawberryGQLContext],
    input: CreateVFolderAutoMountInputGQL,
) -> CreateVFolderAutoMountPayloadGQL | None:
    payload = await info.context.adapters.vfolder_auto_mount.create(input.to_pydantic())
    return CreateVFolderAutoMountPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Change where and how an auto-mounted vfolder is mounted. Sessions created "
            "afterwards follow the change."
        ),
    )
)
async def update_vfolder_auto_mount(
    info: Info[StrawberryGQLContext],
    input: UpdateVFolderAutoMountInputGQL,
) -> UpdateVFolderAutoMountPayloadGQL | None:
    payload = await info.context.adapters.vfolder_auto_mount.update(input.to_pydantic())
    return UpdateVFolderAutoMountPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Mark a vfolder auto-mount deleted. Sessions created afterwards no longer mount it."
        ),
    )
)
async def delete_vfolder_auto_mount(
    info: Info[StrawberryGQLContext],
    input: DeleteVFolderAutoMountInputGQL,
) -> DeleteVFolderAutoMountPayloadGQL | None:
    payload = await info.context.adapters.vfolder_auto_mount.delete(input.to_pydantic())
    return DeleteVFolderAutoMountPayloadGQL.from_pydantic(payload)


def build_vfolder_auto_mount_connection(
    payload: SearchVFolderAutoMountsPayload,
) -> VFolderAutoMountConnectionGQL:
    nodes = [VFolderAutoMountGQL.from_pydantic(item) for item in payload.items]
    edges = [
        VFolderAutoMountEdgeGQL(node=node, cursor=encode_cursor(str(node.id))) for node in nodes
    ]
    return VFolderAutoMountConnectionGQL(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
