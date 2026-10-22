"""Resource Policy V2 GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyUUID,
    UserResourcePolicyUUID,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.resource_policy_v2.types.mutations import (
    CreateKeypairResourcePolicyInputGQL,
    CreateKeypairResourcePolicyPayloadGQL,
    CreateProjectResourcePolicyInputGQL,
    CreateProjectResourcePolicyPayloadGQL,
    CreateUserResourcePolicyInputGQL,
    CreateUserResourcePolicyPayloadGQL,
    DeleteKeypairResourcePolicyPayloadGQL,
    DeleteProjectResourcePolicyPayloadGQL,
    DeleteUserResourcePolicyPayloadGQL,
    PartialBulkKeypairResourcePoliciesPayloadGQL,
    PartialBulkProjectResourcePoliciesPayloadGQL,
    PartialBulkPurgeKeypairResourcePoliciesInputGQL,
    PartialBulkPurgeProjectResourcePoliciesInputGQL,
    PartialBulkPurgeUserResourcePoliciesInputGQL,
    PartialBulkUpdateKeypairResourcePoliciesInputGQL,
    PartialBulkUpdateProjectResourcePoliciesInputGQL,
    PartialBulkUpdateUserResourcePoliciesInputGQL,
    PartialBulkUserResourcePoliciesPayloadGQL,
    PurgeKeypairResourcePolicyPayloadGQL,
    PurgeProjectResourcePolicyPayloadGQL,
    PurgeUserResourcePolicyPayloadGQL,
    UpdateKeypairResourcePolicyInputGQL,
    UpdateKeypairResourcePolicyPayloadGQL,
    UpdateProjectResourcePolicyInputGQL,
    UpdateProjectResourcePolicyPayloadGQL,
    UpdateUserResourcePolicyInputGQL,
    UpdateUserResourcePolicyPayloadGQL,
)
from ai.backend.manager.api.gql.resource_policy_v2.types.node import (
    KeypairResourcePolicyV2GQL,
    ProjectResourcePolicyV2GQL,
    UserResourcePolicyV2GQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# ── Keypair Resource Policy Mutations ──


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a new keypair resource policy (admin only).",
    )
)
async def admin_create_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    input: CreateKeypairResourcePolicyInputGQL,
) -> CreateKeypairResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_create_keypair_resource_policy(
        input.to_pydantic()
    )
    return CreateKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a keypair resource policy. Only provided fields will be updated.",
    )
)
async def update_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateKeypairResourcePolicyInputGQL,
) -> UpdateKeypairResourcePolicyPayloadGQL:
    payload = await info.context.adapters.resource_policy.update_keypair_resource_policy(
        KeyPairResourcePolicyUUID(id), input.to_pydantic()
    )
    return UpdateKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove a keypair resource policy.",
    )
)
async def purge_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeKeypairResourcePolicyPayloadGQL:
    payload = await info.context.adapters.resource_policy.purge_keypair_resource_policy(
        KeyPairResourcePolicyUUID(id)
    )
    return PurgeKeypairResourcePolicyPayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(KeypairResourcePolicyV2GQL, payload.name)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several keypair resource policies, answering for each one.",
    )
)
async def partial_bulk_update_keypair_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateKeypairResourcePoliciesInputGQL,
) -> PartialBulkKeypairResourcePoliciesPayloadGQL:
    adapter = info.context.adapters.resource_policy
    payload = await adapter.partial_bulk_update_keypair_resource_policies(input.to_pydantic())
    return PartialBulkKeypairResourcePoliciesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several keypair resource policies, answering for each one.",
    )
)
async def partial_bulk_purge_keypair_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeKeypairResourcePoliciesInputGQL,
) -> PartialBulkKeypairResourcePoliciesPayloadGQL:
    adapter = info.context.adapters.resource_policy
    payload = await adapter.partial_bulk_purge_keypair_resource_policies(input.to_pydantic())
    return PartialBulkKeypairResourcePoliciesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a keypair resource policy (admin only). Only provided fields will be updated.",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateKeypairResourcePolicyV2`."
    ),
)
async def admin_update_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateKeypairResourcePolicyInputGQL,
) -> UpdateKeypairResourcePolicyPayloadGQL | None:
    check_admin_only()
    adapter = info.context.adapters.resource_policy
    payload = await adapter.update_keypair_resource_policy(
        await adapter.lookup_keypair_resource_policy(name), input.to_pydantic()
    )
    return UpdateKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a keypair resource policy (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeKeypairResourcePolicyV2`."
    ),
)
async def admin_delete_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteKeypairResourcePolicyPayloadGQL | None:
    check_admin_only()
    adapter = info.context.adapters.resource_policy
    payload = await adapter.purge_keypair_resource_policy(
        await adapter.lookup_keypair_resource_policy(name)
    )
    return DeleteKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


# ── User Resource Policy Mutations ──


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a new user resource policy (admin only).",
    )
)
async def admin_create_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    input: CreateUserResourcePolicyInputGQL,
) -> CreateUserResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_create_user_resource_policy(
        input.to_pydantic()
    )
    return CreateUserResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a user resource policy. Only provided fields will be updated.",
    )
)
async def update_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateUserResourcePolicyInputGQL,
) -> UpdateUserResourcePolicyPayloadGQL:
    payload = await info.context.adapters.resource_policy.update_user_resource_policy(
        UserResourcePolicyUUID(id), input.to_pydantic()
    )
    return UpdateUserResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove a user resource policy.",
    )
)
async def purge_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeUserResourcePolicyPayloadGQL:
    payload = await info.context.adapters.resource_policy.purge_user_resource_policy(
        UserResourcePolicyUUID(id)
    )
    return PurgeUserResourcePolicyPayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(UserResourcePolicyV2GQL, payload.name)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several user resource policies, answering for each one.",
    )
)
async def partial_bulk_update_user_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateUserResourcePoliciesInputGQL,
) -> PartialBulkUserResourcePoliciesPayloadGQL:
    adapter = info.context.adapters.resource_policy
    payload = await adapter.partial_bulk_update_user_resource_policies(input.to_pydantic())
    return PartialBulkUserResourcePoliciesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several user resource policies, answering for each one.",
    )
)
async def partial_bulk_purge_user_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeUserResourcePoliciesInputGQL,
) -> PartialBulkUserResourcePoliciesPayloadGQL:
    adapter = info.context.adapters.resource_policy
    payload = await adapter.partial_bulk_purge_user_resource_policies(input.to_pydantic())
    return PartialBulkUserResourcePoliciesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a user resource policy (admin only). Only provided fields will be updated.",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateUserResourcePolicyV2`."
    ),
)
async def admin_update_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateUserResourcePolicyInputGQL,
) -> UpdateUserResourcePolicyPayloadGQL | None:
    check_admin_only()
    adapter = info.context.adapters.resource_policy
    payload = await adapter.update_user_resource_policy(
        await adapter.lookup_user_resource_policy(name), input.to_pydantic()
    )
    return UpdateUserResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a user resource policy (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeUserResourcePolicyV2`."
    ),
)
async def admin_delete_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteUserResourcePolicyPayloadGQL | None:
    check_admin_only()
    adapter = info.context.adapters.resource_policy
    payload = await adapter.purge_user_resource_policy(
        await adapter.lookup_user_resource_policy(name)
    )
    return DeleteUserResourcePolicyPayloadGQL.from_pydantic(payload)


# ── Project Resource Policy Mutations ──


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a new project resource policy (admin only).",
    )
)
async def admin_create_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    input: CreateProjectResourcePolicyInputGQL,
) -> CreateProjectResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_create_project_resource_policy(
        input.to_pydantic()
    )
    return CreateProjectResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a project resource policy. Only provided fields will be updated.",
    )
)
async def update_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
    input: UpdateProjectResourcePolicyInputGQL,
) -> UpdateProjectResourcePolicyPayloadGQL:
    payload = await info.context.adapters.resource_policy.update_project_resource_policy(
        ProjectResourcePolicyUUID(id), input.to_pydantic()
    )
    return UpdateProjectResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove a project resource policy.",
    )
)
async def purge_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeProjectResourcePolicyPayloadGQL:
    payload = await info.context.adapters.resource_policy.purge_project_resource_policy(
        ProjectResourcePolicyUUID(id)
    )
    return PurgeProjectResourcePolicyPayloadGQL.from_pydantic(
        payload, extra={"purged_id": to_global_id(ProjectResourcePolicyV2GQL, payload.name)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update several project resource policies, answering for each one.",
    )
)
async def partial_bulk_update_project_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkUpdateProjectResourcePoliciesInputGQL,
) -> PartialBulkProjectResourcePoliciesPayloadGQL:
    adapter = info.context.adapters.resource_policy
    payload = await adapter.partial_bulk_update_project_resource_policies(input.to_pydantic())
    return PartialBulkProjectResourcePoliciesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several project resource policies, answering for each one.",
    )
)
async def partial_bulk_purge_project_resource_policies_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeProjectResourcePoliciesInputGQL,
) -> PartialBulkProjectResourcePoliciesPayloadGQL:
    adapter = info.context.adapters.resource_policy
    payload = await adapter.partial_bulk_purge_project_resource_policies(input.to_pydantic())
    return PartialBulkProjectResourcePoliciesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a project resource policy (admin only). Only provided fields will be updated.",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `updateProjectResourcePolicyV2`."
    ),
)
async def admin_update_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateProjectResourcePolicyInputGQL,
) -> UpdateProjectResourcePolicyPayloadGQL | None:
    check_admin_only()
    adapter = info.context.adapters.resource_policy
    payload = await adapter.update_project_resource_policy(
        await adapter.lookup_project_resource_policy(name), input.to_pydantic()
    )
    return UpdateProjectResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a project resource policy (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeProjectResourcePolicyV2`."
    ),
)
async def admin_delete_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteProjectResourcePolicyPayloadGQL | None:
    check_admin_only()
    adapter = info.context.adapters.resource_policy
    payload = await adapter.purge_project_resource_policy(
        await adapter.lookup_project_resource_policy(name)
    )
    return DeleteProjectResourcePolicyPayloadGQL.from_pydantic(payload)
