"""Keypair GraphQL mutation resolvers (self-service and admin)."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import UnreachableError
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.keypair.types import (
    AdminCreateKeypairInputGQL,
    AdminCreateKeypairPayloadGQL,
    AdminDeleteKeypairPayloadGQL,
    AdminDeleteSSHKeypairPayloadGQL,
    AdminRegisterSSHKeypairInputGQL,
    AdminRegisterSSHKeypairPayloadGQL,
    AdminUpdateKeypairInputGQL,
    AdminUpdateKeypairPayloadGQL,
    IssueMyKeypairPayloadGQL,
    RevokeMyKeypairInputGQL,
    RevokeMyKeypairPayloadGQL,
    SwitchMyMainAccessKeyInputGQL,
    SwitchMyMainAccessKeyPayloadGQL,
    UpdateMyKeypairInputGQL,
    UpdateMyKeypairPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


def _get_current_user_id() -> UUID:
    me = current_user()
    if me is None:
        raise UnreachableError("User context is not available")
    return me.user_id


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Issue a new keypair for the current user. Settings (resource_policy, rate_limit, is_admin) are inherited from the main keypair. The secret_key is only returned at creation time.",
    )
)  # type: ignore[misc]
async def issue_my_keypair(
    info: Info[StrawberryGQLContext],
) -> IssueMyKeypairPayloadGQL:
    user_id = _get_current_user_id()
    payload = await info.context.adapters.user.issue_my_keypair(user_id)
    return IssueMyKeypairPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Revoke a keypair owned by the current user. The main access key cannot be revoked — switch it first.",
    )
)  # type: ignore[misc]
async def revoke_my_keypair(
    info: Info[StrawberryGQLContext],
    input: RevokeMyKeypairInputGQL,
) -> RevokeMyKeypairPayloadGQL:
    user_id = _get_current_user_id()
    payload = await info.context.adapters.user.revoke_my_keypair(user_id, input.access_key)
    return RevokeMyKeypairPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a keypair owned by the current user (e.g. toggle active state). The keypair must be owned by the current user.",
    )
)  # type: ignore[misc]
async def update_my_keypair(
    info: Info[StrawberryGQLContext],
    input: UpdateMyKeypairInputGQL,
) -> UpdateMyKeypairPayloadGQL:
    user_id = _get_current_user_id()
    payload = await info.context.adapters.user.update_my_keypair(
        user_id, input.access_key, input.is_active
    )
    return UpdateMyKeypairPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Switch the main access key for the current user. The target keypair must be active and owned by the user.",
    )
)  # type: ignore[misc]
async def switch_my_main_access_key(
    info: Info[StrawberryGQLContext],
    input: SwitchMyMainAccessKeyInputGQL,
) -> SwitchMyMainAccessKeyPayloadGQL:
    user_id = _get_current_user_id()
    payload = await info.context.adapters.user.switch_my_main_access_key(user_id, input.access_key)
    return SwitchMyMainAccessKeyPayloadGQL.from_pydantic(payload)


# ------------------------------------------------------------------ admin keypair mutations


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin creates a keypair for a specified user. The secret_key is only returned at creation time.",
    )
)  # type: ignore[misc]
async def admin_create_keypair_v2(
    info: Info[StrawberryGQLContext],
    input: AdminCreateKeypairInputGQL,
) -> AdminCreateKeypairPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.user.admin_create_keypair(input.to_pydantic())
    return AdminCreateKeypairPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin updates a keypair (e.g. toggle active state, change resource policy).",
    )
)  # type: ignore[misc]
async def admin_update_keypair_v2(
    info: Info[StrawberryGQLContext],
    input: AdminUpdateKeypairInputGQL,
) -> AdminUpdateKeypairPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.user.admin_update_keypair(input.to_pydantic())
    return AdminUpdateKeypairPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin deletes a keypair by access key. Cannot delete a main access key.",
    )
)  # type: ignore[misc]
async def admin_delete_keypair_v2(
    info: Info[StrawberryGQLContext],
    access_key: str,
) -> AdminDeleteKeypairPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.user.admin_delete_keypair(access_key)
    return AdminDeleteKeypairPayloadGQL.from_pydantic(payload)


# ------------------------------------------------------------------ admin SSH keypair mutations


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin registers (overwrites) a user's SSH keypair.",
    )
)  # type: ignore[misc]
async def admin_register_ssh_keypair_v2(
    info: Info[StrawberryGQLContext],
    input: AdminRegisterSSHKeypairInputGQL,
) -> AdminRegisterSSHKeypairPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.user.admin_register_ssh_keypair(input.to_pydantic())
    return AdminRegisterSSHKeypairPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Admin clears a user's SSH keypair.",
    )
)  # type: ignore[misc]
async def admin_delete_ssh_keypair_v2(
    info: Info[StrawberryGQLContext],
    access_key: str,
) -> AdminDeleteSSHKeypairPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.user.admin_delete_ssh_keypair(access_key)
    return AdminDeleteSSHKeypairPayloadGQL.from_pydantic(payload)
