"""User V2 GraphQL input types for mutations."""

from __future__ import annotations

from uuid import UUID

import strawberry

from .enums import UserRoleV2EnumGQL, UserStatusV2EnumGQL

# Create User Inputs


@strawberry.input(
    name="CreateUserV2Input",
    description=(
        "Added in 26.2.0. Input for creating a new user. "
        "Required fields: email, username, password, domain_name, need_password_change, status, role."
    ),
)
class CreateUserInputGQL:
    """Input for creating a single user."""

    email: str = strawberry.field(
        description="User's email address. Must be unique across the system."
    )
    username: str = strawberry.field(description="Unique username for login.")
    password: str = strawberry.field(description="Initial password for the user.")
    domain_name: str = strawberry.field(description="Domain to assign the user to.")
    need_password_change: bool = strawberry.field(
        description="If true, user must change password on first login."
    )
    status: UserStatusV2EnumGQL = strawberry.field(description="Initial account status.")
    role: UserRoleV2EnumGQL = strawberry.field(
        description="User role determining access permissions."
    )
    full_name: str | None = strawberry.field(
        default=None,
        description="User's full display name.",
    )
    description: str | None = strawberry.field(
        default=None,
        description="Optional description or notes about the user.",
    )
    group_ids: list[UUID] | None = strawberry.field(
        default=None,
        description="List of project (group) IDs to assign the user to.",
    )
    allowed_client_ip: list[str] | None = strawberry.field(
        default=None,
        description="Allowed client IP addresses or CIDR ranges.",
    )
    totp_activated: bool = strawberry.field(
        default=False,
        description="Whether to enable TOTP two-factor authentication.",
    )
    resource_policy: str = strawberry.field(
        default="default",
        description="Name of the user resource policy to apply.",
    )
    sudo_session_enabled: bool = strawberry.field(
        default=False,
        description="Whether this user can create sudo sessions.",
    )
    container_uid: int | None = strawberry.field(
        default=None,
        description="User ID (UID) for container processes.",
    )
    container_main_gid: int | None = strawberry.field(
        default=None,
        description="Primary group ID (GID) for container processes.",
    )
    container_gids: list[int] | None = strawberry.field(
        default=None,
        description="Supplementary group IDs for container processes.",
    )


@strawberry.input(
    name="BulkCreateUserV2Input",
    description=(
        "Added in 26.2.0. Input for bulk creating multiple users. "
        "Each user has individual specifications."
    ),
)
class BulkCreateUserInputGQL:
    """Input for bulk creating users with individual specs."""

    users: list[CreateUserInputGQL] = strawberry.field(description="List of user creation inputs.")


# Update User Inputs


@strawberry.input(
    name="UpdateUserV2Input",
    description=(
        "Added in 26.2.0. Input for updating user information. "
        "All fields are optional - only provided fields will be updated."
    ),
)
class UpdateUserInputGQL:
    """Input for updating user information. All fields optional."""

    username: str | None = strawberry.field(
        default=None,
        description="New username.",
    )
    password: str | None = strawberry.field(
        default=None,
        description="New password.",
    )
    full_name: str | None = strawberry.field(
        default=None,
        description="New full display name.",
    )
    description: str | None = strawberry.field(
        default=None,
        description="New description.",
    )
    status: UserStatusV2EnumGQL | None = strawberry.field(
        default=None,
        description="New account status.",
    )
    role: UserRoleV2EnumGQL | None = strawberry.field(
        default=None,
        description="New user role.",
    )
    domain_name: str | None = strawberry.field(
        default=None,
        description="New domain assignment.",
    )
    group_ids: list[UUID] | None = strawberry.field(
        default=None,
        description="New project (group) assignments. Replaces existing assignments.",
    )
    allowed_client_ip: list[str] | None = strawberry.field(
        default=None,
        description="New allowed client IP addresses or CIDR ranges.",
    )
    need_password_change: bool | None = strawberry.field(
        default=None,
        description="Set password change requirement.",
    )
    resource_policy: str | None = strawberry.field(
        default=None,
        description="New user resource policy name.",
    )
    sudo_session_enabled: bool | None = strawberry.field(
        default=None,
        description="Enable or disable sudo session capability.",
    )
    main_access_key: str | None = strawberry.field(
        default=None,
        description="Set the primary API access key.",
    )
    container_uid: int | None = strawberry.field(
        default=None,
        description="New container user ID.",
    )
    container_main_gid: int | None = strawberry.field(
        default=None,
        description="New container primary group ID.",
    )
    container_gids: list[int] | None = strawberry.field(
        default=None,
        description="New container supplementary group IDs.",
    )


# Delete User Inputs


@strawberry.input(
    name="DeleteUsersV2Input",
    description=(
        "Added in 26.2.0. Input for soft-deleting multiple users. "
        "Soft delete changes user status to DELETED but preserves data."
    ),
)
class DeleteUsersInputGQL:
    """Input for soft-deleting multiple users."""

    user_ids: list[UUID] = strawberry.field(description="List of user UUIDs to soft-delete.")


# Purge User Inputs


@strawberry.input(
    name="PurgeUserV2Input",
    description=(
        "Added in 26.2.0. Input for permanently deleting a user and all associated data. "
        "This action is irreversible."
    ),
)
class PurgeUserInputGQL:
    """Input for permanently deleting a single user."""

    user_id: UUID = strawberry.field(description="UUID of the user to purge.")


@strawberry.input(
    name="PurgeUsersV2Input",
    description=(
        "Added in 26.2.0. Input for permanently deleting multiple users. "
        "This action is irreversible."
    ),
)
class PurgeUsersInputGQL:
    """Input for permanently deleting multiple users."""

    user_ids: list[UUID] = strawberry.field(description="List of user UUIDs to purge.")
