"""GraphQL root resolver for the system session environ domain."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_mutation, gql_root_field
from ai.backend.manager.api.gql.system_session_environ.types import (
    DeleteSystemSessionEnvironPayloadGQL,
    RestoreSystemSessionEnvironPayloadGQL,
    SystemSessionEnvironConnectionGQL,
    SystemSessionEnvironEdgeGQL,
    SystemSessionEnvironFilterGQL,
    SystemSessionEnvironGQL,
    SystemSessionEnvironOrderByGQL,
    UpdateSystemSessionEnvironInputGQL,
    UpdateSystemSessionEnvironPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Search every system session environ row at every scope, soft-deleted ones included "
            "(superadmin only)."
        ),
    )
)  # type: ignore[misc]
async def admin_system_session_environs(
    info: Info[StrawberryGQLContext],
    filter: SystemSessionEnvironFilterGQL | None = None,
    order_by: list[SystemSessionEnvironOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SystemSessionEnvironConnectionGQL | None:
    check_admin_only()
    payload = await info.context.adapters.system_session_environ.global_search(
        AdminSearchSystemSessionEnvironsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[order.to_pydantic() for order in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [
        SystemSessionEnvironGQL.from_pydantic(item, id_field="entity_id") for item in payload.items
    ]
    edges = [
        SystemSessionEnvironEdgeGQL(node=node, cursor=encode_cursor(str(node.entity_id)))
        for node in nodes
    ]
    return SystemSessionEnvironConnectionGQL(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "List every value source name a system session environ row can carry, the values "
            "``SystemSessionEnviron.valueSource`` holds."
        ),
    )
)  # type: ignore[misc]
async def system_session_environ_value_sources(
    info: Info[StrawberryGQLContext],
) -> list[str] | None:
    payload = await info.context.adapters.system_session_environ.public_list_value_sources()
    return payload.items


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Change a system session environ row's key. Only provided fields are updated."
        ),
    )
)
async def update_system_session_environ(
    info: Info[StrawberryGQLContext],
    input: UpdateSystemSessionEnvironInputGQL,
) -> UpdateSystemSessionEnvironPayloadGQL | None:
    payload = await info.context.adapters.system_session_environ.update(input.to_pydantic())
    return UpdateSystemSessionEnvironPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Soft-delete a system session environ row.",
    )
)
async def delete_system_session_environ(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> DeleteSystemSessionEnvironPayloadGQL | None:
    payload = await info.context.adapters.system_session_environ.delete(SystemSessionEnvironID(id))
    return DeleteSystemSessionEnvironPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Restore a soft-deleted system session environ row.",
    )
)
async def restore_system_session_environ(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> RestoreSystemSessionEnvironPayloadGQL | None:
    payload = await info.context.adapters.system_session_environ.restore(SystemSessionEnvironID(id))
    return RestoreSystemSessionEnvironPayloadGQL.from_pydantic(payload)
