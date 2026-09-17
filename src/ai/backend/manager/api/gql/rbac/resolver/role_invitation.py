"""Deprecated GQL resolvers kept from the removed role invitation feature."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.exception import DeprecatedAPI
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.rbac.types.role_invitation import (
    AcceptRoleInvitationInputGQL,
    CancelRoleInvitationInputGQL,
    CreateRoleInvitationInputGQL,
    CreateRoleInvitationPayloadGQL,
    RejectRoleInvitationInputGQL,
    RoleInvitationConnection,
    RoleInvitationFilterGQL,
    RoleInvitationGQL,
    RoleInvitationOrderByGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

_QUERY_REASON = (
    f"Deprecated since {NEXT_RELEASE_VERSION}. Role invitations are removed;"
    " this connection is always empty."
)
_MUTATION_REASON = (
    f"Deprecated since {NEXT_RELEASE_VERSION}. Role invitations are removed;"
    " this mutation always fails."
)
_REMOVED_MESSAGE = "Role invitations are removed."


def _meta(description: str) -> BackendAIGQLMeta:
    return BackendAIGQLMeta(
        added_version="26.4.4",
        description=description,
        deprecated_version=NEXT_RELEASE_VERSION,
    )


# ==================== Query Resolvers ====================


@gql_root_field(
    _meta("List the current user's role invitations."), deprecation_reason=_QUERY_REASON
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
    return RoleInvitationConnection.empty()


@gql_root_field(
    _meta("List role invitations sent by the current user."), deprecation_reason=_QUERY_REASON
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
    return RoleInvitationConnection.empty()


@gql_root_field(_meta("List invitations for a specific role."), deprecation_reason=_QUERY_REASON)  # type: ignore[misc]
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
    return RoleInvitationConnection.empty()


@gql_root_field(
    _meta("List all role invitations across the system (superadmin only)."),
    deprecation_reason=_QUERY_REASON,
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
    return RoleInvitationConnection.empty()


# ==================== Mutation Resolvers ====================


@gql_mutation(_meta("Create role invitations by email."), deprecation_reason=_MUTATION_REASON)
async def create_role_invitation(
    info: Info[StrawberryGQLContext],
    input: CreateRoleInvitationInputGQL,
) -> CreateRoleInvitationPayloadGQL | None:
    raise DeprecatedAPI(extra_msg=_REMOVED_MESSAGE)


@gql_mutation(_meta("Accept a pending role invitation."), deprecation_reason=_MUTATION_REASON)
async def accept_role_invitation(
    info: Info[StrawberryGQLContext],
    input: AcceptRoleInvitationInputGQL,
) -> RoleInvitationGQL | None:
    raise DeprecatedAPI(extra_msg=_REMOVED_MESSAGE)


@gql_mutation(_meta("Reject a pending role invitation."), deprecation_reason=_MUTATION_REASON)
async def reject_role_invitation(
    info: Info[StrawberryGQLContext],
    input: RejectRoleInvitationInputGQL,
) -> RoleInvitationGQL | None:
    raise DeprecatedAPI(extra_msg=_REMOVED_MESSAGE)


@gql_mutation(
    _meta("Cancel a pending role invitation (admin only)."), deprecation_reason=_MUTATION_REASON
)
async def admin_cancel_role_invitation(
    info: Info[StrawberryGQLContext],
    input: CancelRoleInvitationInputGQL,
) -> RoleInvitationGQL | None:
    check_admin_only()
    raise DeprecatedAPI(extra_msg=_REMOVED_MESSAGE)
