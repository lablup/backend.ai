"""User V2 GraphQL payload types for mutations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import strawberry

from .node import UserV2GQL

if TYPE_CHECKING:
    pass


# Create User Payloads


@strawberry.type(
    name="CreateUserV2Payload",
    description="Added in 26.2.0. Payload for user creation mutation.",
)
class CreateUserV2Payload:
    """Payload for single user creation."""

    user: UserV2GQL = strawberry.field(description="The newly created user.")
    # Note: keypair field can be added when KeyPairGQL is available
    # keypair: KeyPairGQL = strawberry.field(
    #     description="The automatically generated keypair for the user."
    # )


@strawberry.type(
    name="BulkCreateUsersPayload",
    description="Added in 26.2.0. Payload for bulk user creation mutation.",
)
class BulkCreateUsersPayload:
    """Payload for bulk user creation."""

    created_count: int = strawberry.field(description="Number of users successfully created.")
    users: list[UserV2GQL] = strawberry.field(description="List of newly created users.")


# Update User Payloads


@strawberry.type(
    name="UpdateUserV2Payload",
    description="Added in 26.2.0. Payload for user update mutation.",
)
class UpdateUserV2Payload:
    """Payload for user update."""

    user: UserV2GQL = strawberry.field(description="The updated user.")


# Delete User Payloads


@strawberry.type(
    name="DeleteUserPayload",
    description="Added in 26.2.0. Payload for single user soft-delete mutation.",
)
class DeleteUserPayload:
    """Payload for single user soft-delete."""

    success: bool = strawberry.field(description="Whether the deletion was successful.")


@strawberry.type(
    name="DeleteUsersPayload",
    description="Added in 26.2.0. Payload for bulk user soft-delete mutation.",
)
class DeleteUsersPayload:
    """Payload for bulk user soft-delete."""

    deleted_count: int = strawberry.field(description="Number of users successfully soft-deleted.")


# Purge User Payloads


@strawberry.type(
    name="PurgeUserPayload",
    description="Added in 26.2.0. Payload for single user permanent deletion mutation.",
)
class PurgeUserPayload:
    """Payload for single user permanent deletion."""

    success: bool = strawberry.field(description="Whether the purge was successful.")


@strawberry.type(
    name="PurgeUsersPayload",
    description="Added in 26.2.0. Payload for bulk user permanent deletion mutation.",
)
class PurgeUsersPayload:
    """Payload for bulk user permanent deletion."""

    purged_count: int = strawberry.field(description="Number of users successfully purged.")
    failed_user_ids: list[UUID] = strawberry.field(
        description="List of user UUIDs that failed to purge, if any."
    )
