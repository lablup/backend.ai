"""Role preset GQL query resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.role_preset.request import (
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
)
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.role_preset.types import (
    RolePresetConnection,
    RolePresetEdge,
    RolePresetFilterGQL,
    RolePresetGQL,
    RolePresetOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get a single role preset by ID (admin only).",
    )
)  # type: ignore[misc]
async def admin_role_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> RolePresetGQL | None:
    check_admin_only()
    node = await info.context.adapters.role_preset.get(RolePresetID(UUID(str(id))))
    if node is None:
        return None
    return RolePresetGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List role presets with filtering and pagination (admin only).",
    )
)  # type: ignore[misc]
async def admin_role_presets(
    info: Info[StrawberryGQLContext],
    filter: RolePresetFilterGQL | None = None,
    order_by: list[RolePresetOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RolePresetConnection | None:
    check_admin_only()
    filter_dto: RolePresetFilter | None = filter.to_pydantic() if filter else None
    orders_dto: list[RolePresetOrder] | None = (
        [o.to_pydantic() for o in order_by] if order_by else None
    )
    search_input = SearchRolePresetsInput(
        filter=filter_dto,
        order=orders_dto,
        first=first,
        after=after,
        last=last,
        before=before,
        limit=limit,
        offset=offset,
    )
    result = await info.context.adapters.role_preset.search(search_input)
    edges = [
        RolePresetEdge(
            node=RolePresetGQL.from_pydantic(item),
            cursor=str(item.id),
        )
        for item in result.items
    ]
    return RolePresetConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
