"""GraphQL resolvers for role invitation management."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.role_invitation.request import (
    SearchRoleInvitationsInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.rbac.types.role_invitation import (
    AcceptRoleInvitationInputGQL,
    CancelRoleInvitationInputGQL,
    CreateRoleInvitationInputGQL,
    CreateRoleInvitationPayload,
    RejectRoleInvitationInputGQL,
    RoleInvitationConnection,
    RoleInvitationEdge,
    RoleInvitationFilterGQL,
    RoleInvitationGQL,
    RoleInvitationOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# ==================== Query Resolvers ====================


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List the current user's role invitations.",
    )
)  # type: ignore[misc]
async def my_role_invitations(
    info: Info[StrawberryGQLContext],
    filter: RoleInvitationFilterGQL | None = None,
    order_by: list[RoleInvitationOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleInvitationConnection | None:
    result = await info.context.adapters.rbac.my_search_role_invitations(
        SearchRoleInvitationsInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        RoleInvitationEdge(
            node=RoleInvitationGQL.from_pydantic(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return RoleInvitationConnection(
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
        description="List role invitations sent by the current user.",
    )
)  # type: ignore[misc]
async def my_sent_role_invitations(
    info: Info[StrawberryGQLContext],
    filter: RoleInvitationFilterGQL | None = None,
    order_by: list[RoleInvitationOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleInvitationConnection | None:
    result = await info.context.adapters.rbac.my_sent_search_role_invitations(
        SearchRoleInvitationsInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        RoleInvitationEdge(
            node=RoleInvitationGQL.from_pydantic(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return RoleInvitationConnection(
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
        description="List invitations for a specific role.",
    )
)  # type: ignore[misc]
async def role_scoped_role_invitations(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
    filter: RoleInvitationFilterGQL | None = None,
    order_by: list[RoleInvitationOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleInvitationConnection | None:
    result = await info.context.adapters.rbac.role_search_invitations(
        role_id,
        SearchRoleInvitationsInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        RoleInvitationEdge(
            node=RoleInvitationGQL.from_pydantic(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return RoleInvitationConnection(
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
        description="List all role invitations across the system (superadmin only).",
    )
)  # type: ignore[misc]
async def admin_role_invitations(
    info: Info[StrawberryGQLContext],
    filter: RoleInvitationFilterGQL | None = None,
    order_by: list[RoleInvitationOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleInvitationConnection | None:
    check_admin_only()
    result = await info.context.adapters.rbac.admin_search_role_invitations(
        SearchRoleInvitationsInput(
            filter=filter.to_pydantic() if filter is not None else None,
            order=[o.to_pydantic() for o in order_by] if order_by is not None else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
    )
    edges = [
        RoleInvitationEdge(
            node=RoleInvitationGQL.from_pydantic(item),
            cursor=encode_cursor(str(item.id)),
        )
        for item in result.items
    ]
    return RoleInvitationConnection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


# ==================== Mutation Resolvers ====================


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create role invitations by email.",
    )
)
async def create_role_invitation(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInvitationInputGQL,
) -> CreateRoleInvitationPayload | None:
    result = await info.context.adapters.rbac.create_role_invitation(input.to_pydantic())
    return CreateRoleInvitationPayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Accept a pending role invitation.",
    )
)
async def accept_role_invitation(
    info: Info[StrawberryGQLContext],
    input: AcceptRoleInvitationInputGQL,
) -> RoleInvitationGQL | None:
    dto = input.to_pydantic()
    result = await info.context.adapters.rbac.accept_role_invitation(dto.invitation_id)
    return RoleInvitationGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Reject a pending role invitation.",
    )
)
async def reject_role_invitation(
    info: Info[StrawberryGQLContext],
    input: RejectRoleInvitationInputGQL,
) -> RoleInvitationGQL | None:
    dto = input.to_pydantic()
    result = await info.context.adapters.rbac.reject_role_invitation(dto.invitation_id)
    return RoleInvitationGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Cancel a pending role invitation (admin only).",
    )
)
async def admin_cancel_role_invitation(
    info: Info[StrawberryGQLContext],
    input: CancelRoleInvitationInputGQL,
) -> RoleInvitationGQL | None:
    check_admin_only()
    dto = input.to_pydantic()
    result = await info.context.adapters.rbac.cancel_role_invitation(dto.invitation_id)
    return RoleInvitationGQL.from_pydantic(result)
