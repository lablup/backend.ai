from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    ScopedSearchIdleCheckerAssignmentsInput,
    SearchIdleCheckerAssignmentsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.idle_checker_assignment.types import (
    CreateIdleCheckerAssignmentInputGQL,
    CreateIdleCheckerAssignmentPayloadGQL,
    IdleCheckerAssignmentConnectionGQL,
    IdleCheckerAssignmentEdgeGQL,
    IdleCheckerAssignmentFilterGQL,
    IdleCheckerAssignmentGQL,
    IdleCheckerAssignmentOrderByGQL,
    IdleCheckerAssignmentScopeGQL,
    PurgeIdleCheckerAssignmentInputGQL,
    PurgeIdleCheckerAssignmentPayloadGQL,
    UpdateIdleCheckerAssignmentInputGQL,
    UpdateIdleCheckerAssignmentPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches idle checker assignments across all scopes with filtering, ordering, "
            "and pagination (super admin only)."
        ),
    )
)
async def admin_idle_checker_assignments(
    info: Info[StrawberryGQLContext],
    filter: IdleCheckerAssignmentFilterGQL | None = None,
    order_by: list[IdleCheckerAssignmentOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerAssignmentConnectionGQL:
    check_admin_only()
    result = await info.context.adapters.idle_checker_assignment.admin_search(
        SearchIdleCheckerAssignmentsInput(
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
    nodes = [IdleCheckerAssignmentGQL.from_pydantic(item) for item in result.items]
    edges = [
        IdleCheckerAssignmentEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes
    ]
    return IdleCheckerAssignmentConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_root_field(  # type: ignore[misc]
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Searches idle checker assignments within the given scopes. "
            "All scope items are OR'd, at least one item is required, and each item "
            "requires permission on that scope (subject to RBAC)."
        ),
    )
)
async def scoped_idle_checker_assignments(
    info: Info[StrawberryGQLContext],
    scope: IdleCheckerAssignmentScopeGQL,
    filter: IdleCheckerAssignmentFilterGQL | None = None,
    order_by: list[IdleCheckerAssignmentOrderByGQL] | None = None,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> IdleCheckerAssignmentConnectionGQL:
    result = await info.context.adapters.idle_checker_assignment.scoped_search(
        ScopedSearchIdleCheckerAssignmentsInput(
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
    nodes = [IdleCheckerAssignmentGQL.from_pydantic(item) for item in result.items]
    edges = [
        IdleCheckerAssignmentEdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes
    ]
    return IdleCheckerAssignmentConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Binds a global idle checker to a scope (super admin only).",
    )
)
async def admin_create_idle_checker_assignment(
    info: Info[StrawberryGQLContext],
    input: CreateIdleCheckerAssignmentInputGQL,
) -> CreateIdleCheckerAssignmentPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.idle_checker_assignment.admin_create(input.to_pydantic())
    return CreateIdleCheckerAssignmentPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Updates an idle checker assignment's enabled state. "
            "Requires permission on the assignment's scope (subject to RBAC)."
        ),
    )
)
async def update_idle_checker_assignment(
    info: Info[StrawberryGQLContext],
    input: UpdateIdleCheckerAssignmentInputGQL,
) -> UpdateIdleCheckerAssignmentPayloadGQL:
    payload = await info.context.adapters.idle_checker_assignment.update(input.to_pydantic())
    return UpdateIdleCheckerAssignmentPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Permanently removes an idle checker assignment. "
            "Requires permission on the assignment's scope (subject to RBAC)."
        ),
    )
)
async def purge_idle_checker_assignment(
    info: Info[StrawberryGQLContext],
    input: PurgeIdleCheckerAssignmentInputGQL,
) -> PurgeIdleCheckerAssignmentPayloadGQL:
    payload = await info.context.adapters.idle_checker_assignment.purge(input.to_pydantic())
    return PurgeIdleCheckerAssignmentPayloadGQL.from_pydantic(payload)
