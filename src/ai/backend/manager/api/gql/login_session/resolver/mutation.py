"""LoginSession GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.login_session.types.inputs import UpdateLoginSecurityPolicyInputGQL
from ai.backend.manager.api.gql.login_session.types.payloads import (
    RevokeLoginSessionPayloadGQL,
    UpdateUserLoginSecurityPolicyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Update the login security policy for a user (admin only). "
        "Requires superadmin privileges."
    )
)  # type: ignore[misc]
async def update_user_login_security_policy(
    info: Info[StrawberryGQLContext],
    user_id: UUID,
    input: UpdateLoginSecurityPolicyInputGQL,
) -> UpdateUserLoginSecurityPolicyPayloadGQL:
    """Update login security policy for a user.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to update.
        input: Login security policy update input.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    check_admin_only()
    raise NotImplementedError("update_user_login_security_policy is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Revoke a specific login session. "
        "Users may revoke their own sessions; admins may revoke any session."
    )
)  # type: ignore[misc]
async def revoke_login_session(
    info: Info[StrawberryGQLContext],
    session_id: UUID,
) -> RevokeLoginSessionPayloadGQL:
    """Revoke a login session by ID.

    Args:
        info: Strawberry GraphQL context.
        session_id: UUID of the login session to revoke.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("revoke_login_session is not yet implemented")
