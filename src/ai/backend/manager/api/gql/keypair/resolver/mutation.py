"""Keypair self-service GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.gql.keypair.types import (
    IssueMyKeypairPayloadGQL,
    RevokeMyKeypairInputGQL,
    RevokeMyKeypairPayloadGQL,
    SwitchMyMainAccessKeyInputGQL,
    SwitchMyMainAccessKeyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.keypair_ops import (
    IssueMyKeypairAction,
    RevokeMyKeypairAction,
    SwitchMyMainAccessKeyAction,
)


async def _get_my_email(info: Info[StrawberryGQLContext]) -> tuple[UUID, str]:
    """Get current user's UUID and email."""
    me = current_user()
    if me is None:
        raise UnreachableError("User context is not available")
    user_result = await info.context.processors.user.get_user.wait_for_complete(
        GetUserAction(user_uuid=me.user_id)
    )
    return me.user_id, user_result.user.email


@strawberry.mutation(
    description=(
        "Issue a new keypair for the current user. "
        "Settings (resource_policy, rate_limit, is_admin) are inherited from the main keypair. "
        "The secret_key is only returned at creation time."
    )
)  # type: ignore[misc]
async def issue_my_keypair(
    info: Info[StrawberryGQLContext],
) -> IssueMyKeypairPayloadGQL:
    user_uuid, email = await _get_my_email(info)
    result = await info.context.processors.user.issue_my_keypair.wait_for_complete(
        IssueMyKeypairAction(user_uuid=user_uuid, email=email)
    )
    return IssueMyKeypairPayloadGQL(
        access_key=result.generated_data.access_key,
        secret_key=result.generated_data.secret_key,
        ssh_public_key=result.generated_data.ssh_public_key,
    )


@strawberry.mutation(
    description=(
        "Revoke a keypair owned by the current user. "
        "The main access key cannot be revoked — switch it first."
    )
)  # type: ignore[misc]
async def revoke_my_keypair(
    info: Info[StrawberryGQLContext],
    input: RevokeMyKeypairInputGQL,
) -> RevokeMyKeypairPayloadGQL:
    user_uuid, email = await _get_my_email(info)
    result = await info.context.processors.user.revoke_my_keypair.wait_for_complete(
        RevokeMyKeypairAction(user_uuid=user_uuid, email=email, access_key=input.access_key)
    )
    return RevokeMyKeypairPayloadGQL(success=result.success)


@strawberry.mutation(
    description=(
        "Switch the main access key for the current user. "
        "The target keypair must be active and owned by the user."
    )
)  # type: ignore[misc]
async def switch_my_main_access_key(
    info: Info[StrawberryGQLContext],
    input: SwitchMyMainAccessKeyInputGQL,
) -> SwitchMyMainAccessKeyPayloadGQL:
    user_uuid, email = await _get_my_email(info)
    result = await info.context.processors.user.switch_my_main_access_key.wait_for_complete(
        SwitchMyMainAccessKeyAction(user_uuid=user_uuid, email=email, access_key=input.access_key)
    )
    return SwitchMyMainAccessKeyPayloadGQL(success=result.success)
