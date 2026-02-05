"""User V2 GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user_v2.types import (
    BulkCreateUserInputGQL,
    BulkCreateUsersPayloadGQL,
    CreateUserInputGQL,
    CreateUserPayloadGQL,
    DeleteUserPayloadGQL,
    DeleteUsersInputGQL,
    DeleteUsersPayloadGQL,
    PurgeUserInputGQL,
    PurgeUserPayloadGQL,
    PurgeUsersInputGQL,
    PurgeUsersPayloadGQL,
    UpdateUserInputGQL,
    UpdateUserPayloadGQL,
    UserV2GQL,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    BulkUserCreateItem,
)

# Create Mutations


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Create a new user (admin only). "
        "Requires superadmin privileges. "
        "Automatically creates a default keypair for the user."
    )
)  # type: ignore[misc]
async def admin_create_user(
    info: Info[StrawberryGQLContext],
    input: CreateUserInputGQL,
) -> CreateUserPayloadGQL:
    """Create a new user.

    Args:
        info: Strawberry GraphQL context.
        input: User creation input.

    Returns:
        CreateUserPayload with the created user.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("admin_create_user is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Create multiple users in bulk (admin only). "
        "Requires superadmin privileges. "
        "Each user has individual specifications."
    )
)  # type: ignore[misc]
async def admin_bulk_create_users(
    info: Info[StrawberryGQLContext],
    input: BulkCreateUserInputGQL,
) -> BulkCreateUsersPayloadGQL:
    """Create multiple users in bulk with individual specifications.

    Args:
        info: Strawberry GraphQL context.
        input: Bulk user creation input with individual specs.

    Returns:
        BulkCreateUsersPayload with created users.
    """
    ctx = info.context
    auth_config = ctx.config_provider.config.auth

    # Build list of BulkUserCreateItem from input
    items: list[BulkUserCreateItem] = []
    for user_input in input.users:
        password_info = PasswordInfo(
            password=user_input.password,
            algorithm=auth_config.password_hash_algorithm,
            rounds=auth_config.password_hash_rounds,
            salt_size=auth_config.password_hash_salt_size,
        )

        spec = UserCreatorSpec(
            email=user_input.email,
            username=user_input.username,
            password=password_info,
            need_password_change=user_input.need_password_change,
            domain_name=user_input.domain_name,
            full_name=user_input.full_name,
            description=user_input.description,
            status=UserStatus(user_input.status.value),
            role=user_input.role.value,
            allowed_client_ip=user_input.allowed_client_ip,
            totp_activated=user_input.totp_activated,
            resource_policy=user_input.resource_policy,
            sudo_session_enabled=user_input.sudo_session_enabled,
            container_uid=user_input.container_uid,
            container_main_gid=user_input.container_main_gid,
            container_gids=user_input.container_gids,
        )

        group_ids = [str(gid) for gid in user_input.group_ids] if user_input.group_ids else None
        items.append(BulkUserCreateItem(creator=Creator(spec=spec), group_ids=group_ids))

    action = BulkCreateUserAction(items=items)
    result = await ctx.processors.user.bulk_create_users.wait_for_complete(action)

    users = [UserV2GQL.from_data(user_data) for user_data in result.data.successes]

    return BulkCreateUsersPayloadGQL(
        created_count=result.data.success_count(),
        users=users,
    )


# Update Mutations


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Update a user's information (admin only). "
        "Requires superadmin privileges. "
        "Only provided fields will be updated."
    )
)  # type: ignore[misc]
async def admin_update_user(
    info: Info[StrawberryGQLContext],
    user_id: UUID,
    input: UpdateUserInputGQL,
) -> UpdateUserPayloadGQL:
    """Update a user's information.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to update.
        input: User update input with fields to modify.

    Returns:
        UpdateUserPayload with the updated user.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("admin_update_user is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Update the current user's information. "
        "Users can only update their own profile. "
        "Some fields may be restricted based on user role."
    )
)  # type: ignore[misc]
async def update_user(
    info: Info[StrawberryGQLContext],
    input: UpdateUserInputGQL,
) -> UpdateUserPayloadGQL:
    """Update the current user's own information.

    Args:
        info: Strawberry GraphQL context.
        input: User update input with fields to modify.

    Returns:
        UpdateUserPayload with the updated user.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("update_user is not yet implemented")


# Delete Mutations (Soft Delete)


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Soft-delete a user (admin only). "
        "Requires superadmin privileges. "
        "Sets the user status to DELETED but preserves data."
    )
)  # type: ignore[misc]
async def admin_delete_user(
    info: Info[StrawberryGQLContext],
    user_id: UUID,
) -> DeleteUserPayloadGQL:
    """Soft-delete a single user.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to delete.

    Returns:
        DeleteUserPayload indicating success.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("admin_delete_user is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Soft-delete multiple users (admin only). "
        "Requires superadmin privileges. "
        "Sets user status to DELETED but preserves data."
    )
)  # type: ignore[misc]
async def admin_delete_users(
    info: Info[StrawberryGQLContext],
    input: DeleteUsersInputGQL,
) -> DeleteUsersPayloadGQL:
    """Soft-delete multiple users.

    Args:
        info: Strawberry GraphQL context.
        input: Input containing list of user UUIDs to delete.

    Returns:
        DeleteUsersPayload with count of deleted users.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("admin_delete_users is not yet implemented")


# Purge Mutations (Hard Delete)


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Permanently delete a user and all associated data (admin only). "
        "Requires superadmin privileges. "
        "This action is IRREVERSIBLE. All user data, sessions, and resources will be deleted."
    )
)  # type: ignore[misc]
async def admin_purge_user(
    info: Info[StrawberryGQLContext],
    input: PurgeUserInputGQL,
) -> PurgeUserPayloadGQL:
    """Permanently delete a single user.

    Args:
        info: Strawberry GraphQL context.
        input: Purge input with email and options.

    Returns:
        PurgeUserPayload indicating success.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("admin_purge_user is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Permanently delete multiple users (admin only). "
        "Requires superadmin privileges. "
        "This action is IRREVERSIBLE. All user data will be deleted."
    )
)  # type: ignore[misc]
async def admin_purge_users(
    info: Info[StrawberryGQLContext],
    input: PurgeUsersInputGQL,
) -> PurgeUsersPayloadGQL:
    """Permanently delete multiple users.

    Args:
        info: Strawberry GraphQL context.
        input: Purge input with emails and options.

    Returns:
        PurgeUsersPayload with count of purged users.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("admin_purge_users is not yet implemented")
