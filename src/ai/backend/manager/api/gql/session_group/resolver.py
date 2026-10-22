"""Session group GraphQL query and mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.session_group.request import (
    AdminSearchSessionGroupsInput,
    ScopedSearchSessionGroupsInput,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    AdminSearchSessionGroupsPayload,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor, to_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.session_group.types import (
    CreateSessionGroupInputGQL,
    CreateSessionGroupPayloadGQL,
    PurgeSessionGroupInputGQL,
    PurgeSessionGroupPayloadGQL,
    SessionGroupConnectionGQL,
    SessionGroupEdgeGQL,
    SessionGroupFilterGQL,
    SessionGroupGQL,
    SessionGroupOrderByGQL,
    SessionGroupScopeGQL,
    UpdateSessionGroupInputGQL,
    UpdateSessionGroupPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Get a single session group by ID. A group a deployment's replica group holds "
            "is not found."
        ),
    )
)  # type: ignore[misc]
async def session_group(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> SessionGroupGQL | None:
    node = await info.context.adapters.session_group.get(SessionGroupID(id))
    return SessionGroupGQL.from_pydantic(node)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Search every session group, deployment groups included (superadmin only). "
            "Groups marked deleted are left out unless the filter names `deletedAt`."
        ),
    )
)  # type: ignore[misc]
async def admin_session_groups(
    info: Info[StrawberryGQLContext],
    filter: SessionGroupFilterGQL | None = None,
    order_by: list[SessionGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionGroupConnectionGQL | None:
    check_admin_only()
    payload = await info.context.adapters.session_group.global_search(
        AdminSearchSessionGroupsInput(
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
    return _build_connection(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Page through the session groups the named scopes reach, combined with OR. "
            "Every scope is authorized before the read runs, and groups a deployment's "
            "replica group holds are left out."
        ),
    )
)  # type: ignore[misc]
async def scoped_session_groups(
    info: Info[StrawberryGQLContext],
    scope: SessionGroupScopeGQL,
    filter: SessionGroupFilterGQL | None = None,
    order_by: list[SessionGroupOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionGroupConnectionGQL | None:
    payload = await info.context.adapters.session_group.scoped_search(
        ScopedSearchSessionGroupsInput(
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
    return _build_connection(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Change a session group's placement direction and enforcement. Members placed "
            "afterwards follow the new policy; a group a deployment's replica group holds "
            "is refused as in use."
        ),
    )
)
async def update_session_group(
    info: Info[StrawberryGQLContext],
    input: UpdateSessionGroupInputGQL,
) -> UpdateSessionGroupPayloadGQL | None:
    payload = await info.context.adapters.session_group.update(input.to_pydantic())
    return UpdateSessionGroupPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Create a session group in a project. The caller becomes its owner; the caller "
            "needs the session group create permission on the project."
        ),
    )
)
async def create_session_group(
    info: Info[StrawberryGQLContext],
    input: CreateSessionGroupInputGQL,
) -> CreateSessionGroupPayloadGQL | None:
    payload = await info.context.adapters.session_group.create(input.to_pydantic())
    return CreateSessionGroupPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Permanently remove a session group. Its member sessions remain with their group "
            "cleared. A group a deployment's replica group references is refused as in use."
        ),
    )
)
async def purge_session_group(
    info: Info[StrawberryGQLContext],
    input: PurgeSessionGroupInputGQL,
) -> PurgeSessionGroupPayloadGQL | None:
    payload = await info.context.adapters.session_group.purge(input.to_pydantic())
    return PurgeSessionGroupPayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(SessionGroupGQL, payload.entity_id)}
    )


def _build_connection(payload: AdminSearchSessionGroupsPayload) -> SessionGroupConnectionGQL:
    nodes = [SessionGroupGQL.from_pydantic(item) for item in payload.items]
    edges = [SessionGroupEdgeGQL(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]
    return SessionGroupConnectionGQL(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )
