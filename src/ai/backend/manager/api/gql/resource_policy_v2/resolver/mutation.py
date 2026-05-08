"""Resource Policy V2 GraphQL mutation resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    DeleteKeypairResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    DeleteUserResourcePolicyInput,
)
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
        added_version="26.4.2",
        description="Update a keypair resource policy (admin only). Only provided fields will be updated.",
    )
)
async def admin_update_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateKeypairResourcePolicyInputGQL,
) -> UpdateKeypairResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_update_keypair_resource_policy(
        name, input.to_pydantic()
    )
    return UpdateKeypairResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a keypair resource policy (admin only).",
    )
)
async def admin_delete_keypair_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteKeypairResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_delete_keypair_resource_policy(
        DeleteKeypairResourcePolicyInput(name=name)
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
        added_version="26.4.2",
        description="Update a user resource policy (admin only). Only provided fields will be updated.",
    )
)
async def admin_update_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateUserResourcePolicyInputGQL,
) -> UpdateUserResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_update_user_resource_policy(
        name, input.to_pydantic()
    )
    return UpdateUserResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a user resource policy (admin only).",
    )
)
async def admin_delete_user_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteUserResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_delete_user_resource_policy(
        DeleteUserResourcePolicyInput(name=name)
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
        added_version="26.4.2",
        description="Update a project resource policy (admin only). Only provided fields will be updated.",
    )
)
async def admin_update_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
    input: UpdateProjectResourcePolicyInputGQL,
) -> UpdateProjectResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_update_project_resource_policy(
        name, input.to_pydantic()
    )
    return UpdateProjectResourcePolicyPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a project resource policy (admin only).",
    )
)
async def admin_delete_project_resource_policy_v2(
    info: Info[StrawberryGQLContext],
    name: str,
) -> DeleteProjectResourcePolicyPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.resource_policy.admin_delete_project_resource_policy(
        DeleteProjectResourcePolicyInput(name=name)
    )
    return DeleteProjectResourcePolicyPayloadGQL.from_pydantic(payload)
