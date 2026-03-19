"""User GraphQL payload types for mutations."""

from __future__ import annotations

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

from .node import UserV2GQL

# Create User Payloads


@strawberry.type(
    name="CreateUserV2Payload",
    description="Added in 26.2.0. Payload for user creation mutation.",
)
class CreateUserPayloadGQL:
    """Payload for single user creation."""

    user: UserV2GQL = strawberry.field(description="The newly created user.")
    # Note: keypair field can be added when KeyPairGQL is available
    # keypair: KeyPairGQL = strawberry.field(
    #     description="The automatically generated keypair for the user."
    # )


@strawberry.experimental.pydantic.type(
    model=BulkCreateUserV2ErrorDTO,
    name="BulkCreateUserV2Error",
    description="Added in 26.2.0. Error information for a failed user in bulk creation.",
    all_fields=True,
)
class BulkCreateUserV2ErrorGQL:
    """Error information for a single user that failed during bulk creation."""


@strawberry.type(
    name="BulkCreateUsersV2Payload",
    description="Added in 26.2.0. Payload for bulk user creation mutation.",
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


@strawberry.type(
    name="UpdateUserV2Payload",
    description="Added in 26.3.0. Payload for user update mutation.",
)
class UpdateUserPayloadGQL:
    """Payload for user update."""

    user: UserV2GQL = strawberry.field(description="The updated user.")


@strawberry.experimental.pydantic.type(
    model=BulkUpdateUserV2ErrorDTO,
    name="BulkUpdateUserV2Error",
    description="Added in 26.3.0. Error information for a failed user in bulk update.",
    all_fields=True,
)
class BulkUpdateUserV2ErrorGQL:
    """Error information for a single user that failed during bulk update."""


@strawberry.type(
    name="BulkUpdateUsersV2Payload",
    description="Added in 26.3.0. Payload for bulk user update mutation.",
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


@strawberry.experimental.pydantic.type(
    model=DeleteUserPayloadDTO,
    name="DeleteUserV2Payload",
    description="Added in 26.2.0. Payload for single user soft-delete mutation.",
    all_fields=True,
)
class DeleteUserPayloadGQL:
    """Payload for single user soft-delete."""


@strawberry.experimental.pydantic.type(
    model=DeleteUsersPayloadDTO,
    name="DeleteUsersV2Payload",
    description="Added in 26.2.0. Payload for bulk user soft-delete mutation.",
    all_fields=True,
)
class DeleteUsersPayloadGQL:
    """Payload for bulk user soft-delete."""


# Purge User Payloads


@strawberry.experimental.pydantic.type(
    model=PurgeUserPayloadDTO,
    name="PurgeUserV2Payload",
    description="Added in 26.2.0. Payload for single user permanent deletion mutation.",
    all_fields=True,
)
class PurgeUserPayloadGQL:
    """Payload for single user permanent deletion."""


@strawberry.experimental.pydantic.type(
    model=PurgeUsersPayloadDTO,
    name="PurgeUsersV2Payload",
    description="Added in 26.2.0. Payload for bulk user permanent deletion mutation.",
    all_fields=True,
)
class PurgeUsersPayloadGQL:
    """Payload for bulk user permanent deletion."""


@strawberry.experimental.pydantic.type(
    model=BulkPurgeUserV2ErrorDTO,
    name="BulkPurgeUserV2Error",
    description="Added in 26.3.0. Error information for a failed user in bulk purge.",
    all_fields=True,
)
class BulkPurgeUserV2ErrorGQL:
    """Error information for a single user that failed during bulk purge."""


@strawberry.experimental.pydantic.type(
    model=BulkPurgeUsersPayloadDTO,
    name="BulkPurgeUsersV2Payload",
    description="Added in 26.3.0. Payload for bulk user permanent deletion mutation.",
)
class BulkPurgeUsersV2PayloadGQL:
    """Payload for bulk user permanent deletion."""

    purged_count: int = strawberry.field(description="Number of users successfully purged.")
    failed: list[BulkPurgeUserV2ErrorGQL] = strawberry.field(
        description="List of errors for users that failed to purge."
    )


# IP Allowlist Payloads


@strawberry.experimental.pydantic.type(
    model=UpdateMyAllowedClientIPPayloadDTO,
    name="UpdateMyAllowedClientIPPayload",
    description="Added in 26.4.0. Payload for updating the current user's allowed client IP list.",
    all_fields=True,
)
class UpdateMyAllowedClientIPPayloadGQL:
    """Payload for updating the current user's allowed client IP list."""
