"""User V2 GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user_v2.types import (
    BulkCreateUsersPayload,
    BulkCreateUserV2Input,
    CreateUserV2Input,
    CreateUserV2Payload,
    DeleteUserPayload,
    DeleteUsersPayload,
    DeleteUsersV2Input,
    PurgeUserPayload,
    PurgeUsersPayload,
    PurgeUsersV2Input,
    PurgeUserV2Input,
    UpdateUserV2Input,
    UpdateUserV2Payload,
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
    input: CreateUserV2Input,
) -> CreateUserV2Payload:
    """Create a new user.

    Args:
        info: Strawberry GraphQL context.
        input: User creation input.

    Returns:
        CreateUserV2Payload with the created user.

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
    input: BulkCreateUserV2Input,
) -> BulkCreateUsersPayload:
    """Create multiple users in bulk with individual specifications.

    Args:
        info: Strawberry GraphQL context.
        input: Bulk user creation input with individual specs.

    Returns:
        BulkCreateUsersPayload with created users.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("admin_bulk_create_users is not yet implemented")


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
    input: UpdateUserV2Input,
) -> UpdateUserV2Payload:
    """Update a user's information.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to update.
        input: User update input with fields to modify.

    Returns:
        UpdateUserV2Payload with the updated user.

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
    input: UpdateUserV2Input,
) -> UpdateUserV2Payload:
    """Update the current user's own information.

    Args:
        info: Strawberry GraphQL context.
        input: User update input with fields to modify.

    Returns:
        UpdateUserV2Payload with the updated user.

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
) -> DeleteUserPayload:
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
    input: DeleteUsersV2Input,
) -> DeleteUsersPayload:
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
    input: PurgeUserV2Input,
) -> PurgeUserPayload:
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
    input: PurgeUsersV2Input,
) -> PurgeUsersPayload:
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
