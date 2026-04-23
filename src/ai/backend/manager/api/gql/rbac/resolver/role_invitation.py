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
    CreateRoleInvitationInput,
    CreateRoleInvitationPayload,
    RoleInvitationConnection,
    RoleInvitationEdge,
    RoleInvitationGQL,
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
    limit: int | None = None,
    offset: int | None = None,
) -> RoleInvitationConnection:
    result = await info.context.adapters.rbac.my_search_role_invitations(
        SearchRoleInvitationsInput(limit=limit, offset=offset),
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
        description="List invitations for a specific role (admin only).",
    )
)  # type: ignore[misc]
async def admin_role_invitations(
    info: Info[StrawberryGQLContext],
    role_id: UUID,
    limit: int | None = None,
    offset: int | None = None,
) -> RoleInvitationConnection:
    check_admin_only()
    result = await info.context.adapters.rbac.role_search_invitations(
        role_id,
        SearchRoleInvitationsInput(limit=limit, offset=offset),
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
)  # type: ignore[misc]
async def create_role_invitation(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInvitationInput,
) -> CreateRoleInvitationPayload:
    result = await info.context.adapters.rbac.create_role_invitation(input.to_pydantic())
    return CreateRoleInvitationPayload.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Accept a pending role invitation.",
    )
)  # type: ignore[misc]
async def accept_role_invitation(
    info: Info[StrawberryGQLContext],
    invitation_id: UUID,
) -> RoleInvitationGQL:
    result = await info.context.adapters.rbac.accept_role_invitation(invitation_id)
    return RoleInvitationGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Reject a pending role invitation.",
    )
)  # type: ignore[misc]
async def reject_role_invitation(
    info: Info[StrawberryGQLContext],
    invitation_id: UUID,
) -> RoleInvitationGQL:
    result = await info.context.adapters.rbac.reject_role_invitation(invitation_id)
    return RoleInvitationGQL.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Cancel a pending role invitation (admin only).",
    )
)  # type: ignore[misc]
async def admin_cancel_role_invitation(
    info: Info[StrawberryGQLContext],
    invitation_id: UUID,
) -> RoleInvitationGQL:
    check_admin_only()
    result = await info.context.adapters.rbac.cancel_role_invitation(invitation_id)
    return RoleInvitationGQL.from_pydantic(result)
