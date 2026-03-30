"""Resource Policy V2 GraphQL mutation resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    DeleteKeypairResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    DeleteUserResourcePolicyInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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
    UpdateKeypairResourcePolicyInputGQL,
    UpdateKeypairResourcePolicyPayloadGQL,
    UpdateProjectResourcePolicyInputGQL,
    UpdateProjectResourcePolicyPayloadGQL,
    UpdateUserResourcePolicyInputGQL,
    UpdateUserResourcePolicyPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

# ── Keypair Resource Policy Mutations ──


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new keypair resource policy (admin only).",
    )
)  # type: ignore[misc]
async def admin_create_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    input: CreateKeypairResourcePolicyInputGQL,
) -> CreateKeypairResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_create_keypair_resource_policy(
        input.to_pydantic()
    )
    return CreateKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a keypair resource policy (admin only). Only provided fields will be updated.",
    )
)  # type: ignore[misc]
async def admin_update_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateKeypairResourcePolicyInputGQL,
) -> UpdateKeypairResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_update_keypair_resource_policy(
        name, input.to_pydantic()
    )
    return UpdateKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a keypair resource policy (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteKeypairResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_delete_keypair_resource_policy(
        DeleteKeypairResourcePolicyInput(name=name)
    )
    return DeleteKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


# ── User Resource Policy Mutations ──


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new user resource policy (admin only).",
    )
)  # type: ignore[misc]
async def admin_create_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    input: CreateUserResourcePolicyInputGQL,
) -> CreateUserResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_create_user_resource_policy(
        input.to_pydantic()
    )
    return CreateUserResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a user resource policy (admin only). Only provided fields will be updated.",
    )
)  # type: ignore[misc]
async def admin_update_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateUserResourcePolicyInputGQL,
) -> UpdateUserResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_update_user_resource_policy(
        name, input.to_pydantic()
    )
    return UpdateUserResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a user resource policy (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteUserResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_delete_user_resource_policy(
        DeleteUserResourcePolicyInput(name=name)
    )
    return DeleteUserResourcePolicyPayloadGQL.from_pydantic(payload)


# ── Project Resource Policy Mutations ──


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Create a new project resource policy (admin only).",
    )
)  # type: ignore[misc]
async def admin_create_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    input: CreateProjectResourcePolicyInputGQL,
) -> CreateProjectResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_create_project_resource_policy(
        input.to_pydantic()
    )
    return CreateProjectResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Update a project resource policy (admin only). Only provided fields will be updated.",
    )
)  # type: ignore[misc]
async def admin_update_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateProjectResourcePolicyInputGQL,
) -> UpdateProjectResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_update_project_resource_policy(
        name, input.to_pydantic()
    )
    return UpdateProjectResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Delete a project resource policy (admin only).",
    )
)  # type: ignore[misc]
async def admin_delete_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteProjectResourcePolicyPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_delete_project_resource_policy(
        DeleteProjectResourcePolicyInput(name=name)
    )
    return DeleteProjectResourcePolicyPayloadGQL.from_pydantic(payload)
