"""User GraphQL payload types for mutations."""

from __future__ import annotations

from uuid import UUID

import strawberry

from ai.backend.common.dto.manager.v2.user.response import (
    BulkCreateUserV2Error as BulkCreateUserV2ErrorDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    BulkPurgeUsersPayload as BulkPurgeUsersPayloadDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    BulkPurgeUserV2Error as BulkPurgeUserV2ErrorDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    BulkUpdateUserV2Error as BulkUpdateUserV2ErrorDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    DeleteUserPayload as DeleteUserPayloadDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    DeleteUsersPayload as DeleteUsersPayloadDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    PurgeUserPayload as PurgeUserPayloadDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    PurgeUsersPayload as PurgeUsersPayloadDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UpdateMyAllowedClientIPPayload as UpdateMyAllowedClientIPPayloadDTO,
)
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_node_type, gql_pydantic_type

from .node import UserV2GQL

# Create User Payloads


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload for user creation mutation.",
    ),
    name="CreateUserV2Payload",
)
class CreateUserPayloadGQL:
    """Payload for single user creation."""

    user: UserV2GQL = strawberry.field(description="The newly created user.")
    # Note: keypair field can be added when KeyPairGQL is available
    # keypair: KeyPairGQL = strawberry.field(
    #     description="The automatically generated keypair for the user."
    # )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Error information for a failed user in bulk creation.",
    ),
    model=BulkCreateUserV2ErrorDTO,
    name="BulkCreateUserV2Error",
)
class BulkCreateUserV2ErrorGQL:
    """Error information for a single user that failed during bulk creation."""

    index: int = strawberry.field(description="Original position in the input list.")
    username: str = strawberry.field(description="Username of the user that failed.")
    email: str = strawberry.field(description="Email of the user that failed.")
    message: str = strawberry.field(description="Error message describing the failure.")


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload for bulk user creation mutation.",
    ),
    name="BulkCreateUsersV2Payload",
)
class BulkCreateUsersV2PayloadGQL:
    """Payload for bulk user creation."""

    created_users: list[UserV2GQL] = strawberry.field(
        description="List of successfully created users."
    )
    failed: list[BulkCreateUserV2ErrorGQL] = strawberry.field(
        description="List of errors for users that failed to create."
    )


# Update User Payloads


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload for user update mutation.",
    ),
    name="UpdateUserV2Payload",
)
class UpdateUserPayloadGQL:
    """Payload for user update."""

    user: UserV2GQL = strawberry.field(description="The updated user.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Error information for a failed user in bulk update.",
    ),
    model=BulkUpdateUserV2ErrorDTO,
    name="BulkUpdateUserV2Error",
)
class BulkUpdateUserV2ErrorGQL:
    """Error information for a single user that failed during bulk update."""

    user_id: UUID = strawberry.field(description="UUID of the user that failed to update.")
    message: str = strawberry.field(description="Error message describing the failure.")


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload for bulk user update mutation.",
    ),
    name="BulkUpdateUsersV2Payload",
)
class BulkUpdateUsersV2PayloadGQL:
    """Payload for bulk user update."""

    updated_users: list[UserV2GQL] = strawberry.field(
        description="List of successfully updated users."
    )
    failed: list[BulkUpdateUserV2ErrorGQL] = strawberry.field(
        description="List of errors for users that failed to update."
    )


# Delete User Payloads


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload for single user soft-delete mutation.",
    ),
    model=DeleteUserPayloadDTO,
    name="DeleteUserV2Payload",
)
class DeleteUserPayloadGQL:
    """Payload for single user soft-delete."""

    success: bool = strawberry.field(description="Whether the deletion was successful.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload for bulk user soft-delete mutation.",
    ),
    model=DeleteUsersPayloadDTO,
    name="DeleteUsersV2Payload",
)
class DeleteUsersPayloadGQL:
    """Payload for bulk user soft-delete."""

    deleted_count: int = strawberry.field(description="Number of users successfully soft-deleted.")


# Purge User Payloads


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload for single user permanent deletion mutation.",
    ),
    model=PurgeUserPayloadDTO,
    name="PurgeUserV2Payload",
)
class PurgeUserPayloadGQL:
    """Payload for single user permanent deletion."""

    success: bool = strawberry.field(description="Whether the purge was successful.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Payload for bulk user permanent deletion mutation.",
    ),
    model=PurgeUsersPayloadDTO,
    name="PurgeUsersV2Payload",
)
class PurgeUsersPayloadGQL:
    """Payload for bulk user permanent deletion."""

    purged_count: int = strawberry.field(description="Number of users successfully purged.")
    failed_user_ids: list[UUID] = strawberry.field(
        description="List of user UUIDs that failed to purge, if any."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Error information for a failed user in bulk purge.",
    ),
    model=BulkPurgeUserV2ErrorDTO,
    name="BulkPurgeUserV2Error",
)
class BulkPurgeUserV2ErrorGQL:
    """Error information for a single user that failed during bulk purge."""

    user_id: UUID = strawberry.field(description="UUID of the user that failed to purge.")
    message: str = strawberry.field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload for bulk user permanent deletion mutation.",
    ),
    model=BulkPurgeUsersPayloadDTO,
    name="BulkPurgeUsersV2Payload",
)
class BulkPurgeUsersV2PayloadGQL:
    """Payload for bulk user permanent deletion."""

    purged_count: int = strawberry.field(description="Number of users successfully purged.")
    failed: list[BulkPurgeUserV2ErrorGQL] = strawberry.field(
        description="List of errors for users that failed to purge."
    )


# IP Allowlist Payloads


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.0",
        description="Payload for updating the current user's allowed client IP list.",
    ),
    model=UpdateMyAllowedClientIPPayloadDTO,
    name="UpdateMyAllowedClientIPPayload",
)
class UpdateMyAllowedClientIPPayloadGQL:
    """Payload for updating the current user's allowed client IP list."""

    success: bool = strawberry.field(description="Whether the update was successful.")
