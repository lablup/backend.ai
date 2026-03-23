"""User GraphQL input types for mutations."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import UNSET

from ai.backend.common.dto.manager.v2.user.request import (
    BulkCreateUsersInput as BulkCreateUsersInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    BulkPurgeUsersInput as BulkPurgeUsersInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    BulkPurgeUsersOptions as BulkPurgeUsersOptionsDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    BulkUpdateUserItemInput as BulkUpdateUserItemInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    BulkUpdateUsersInput as BulkUpdateUsersInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    CreateUserInput as CreateUserInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    DeleteUsersInput as DeleteUsersInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    PurgeUserV2Input as PurgeUserV2InputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    UpdateMyAllowedClientIPInput as UpdateMyAllowedClientIPInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    UpdateUserInput as UpdateUserInputDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .enums import UserRoleEnumGQL, UserStatusEnumGQL

# Create User Inputs


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a new user. Required fields: email, username, password, domain_name, need_password_change, status, role.",
        added_version="26.2.0",
    ),
    name="CreateUserV2Input",
)
class CreateUserInputGQL(PydanticInputMixin[CreateUserInputDTO]):
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
    status: UserStatusEnumGQL = strawberry.field(description="Initial account status.")
    role: UserRoleEnumGQL = strawberry.field(
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk creating multiple users. Each user has individual specifications.",
        added_version="26.2.0",
    ),
    name="BulkCreateUserV2Input",
)
class BulkCreateUserV2InputGQL(PydanticInputMixin[BulkCreateUsersInputDTO]):
    """Input for bulk creating users with individual specs."""

    users: list[CreateUserInputGQL] = strawberry.field(description="List of user creation inputs.")


# Update User Inputs


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating user information. All fields are optional - only provided fields will be updated.",
        added_version="26.3.0",
    ),
    name="UpdateUserV2Input",
)
class UpdateUserV2InputGQL(PydanticInputMixin[UpdateUserInputDTO]):
    """Input for updating user information. All fields optional."""

    username: str | None = strawberry.field(
        default=UNSET,
        description="New username.",
    )
    password: str | None = strawberry.field(
        default=UNSET,
        description="New password.",
    )
    full_name: str | None = strawberry.field(
        default=UNSET,
        description="New full display name.",
    )
    description: str | None = strawberry.field(
        default=UNSET,
        description="New description.",
    )
    status: UserStatusEnumGQL | None = strawberry.field(
        default=UNSET,
        description="New account status.",
    )
    role: UserRoleEnumGQL | None = strawberry.field(
        default=UNSET,
        description="New user role.",
    )
    domain_name: str | None = strawberry.field(
        default=UNSET,
        description="New domain assignment.",
    )
    group_ids: list[UUID] | None = strawberry.field(
        default=UNSET,
        description="New project (group) assignments. Replaces existing assignments.",
    )
    allowed_client_ip: list[str] | None = strawberry.field(
        default=UNSET,
        description="New allowed client IP addresses or CIDR ranges.",
    )
    need_password_change: bool | None = strawberry.field(
        default=UNSET,
        description="Set password change requirement.",
    )
    resource_policy: str | None = strawberry.field(
        default=UNSET,
        description="New user resource policy name.",
    )
    sudo_session_enabled: bool | None = strawberry.field(
        default=UNSET,
        description="Enable or disable sudo session capability.",
    )
    main_access_key: str | None = strawberry.field(
        default=UNSET,
        description="Set the primary API access key.",
    )
    container_uid: int | None = strawberry.field(
        default=UNSET,
        description="New container user ID.",
    )
    container_main_gid: int | None = strawberry.field(
        default=UNSET,
        description="New container primary group ID.",
    )
    container_gids: list[int] | None = strawberry.field(
        default=UNSET,
        description="New container supplementary group IDs.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for a single user update within a bulk operation. Pairs a user ID with the fields to update.",
        added_version="26.3.0",
    ),
    name="BulkUpdateUserV2ItemInput",
)
class BulkUpdateUserV2ItemInputGQL(PydanticInputMixin[BulkUpdateUserItemInputDTO]):
    """Input for a single user update in bulk operation."""

    user_id: UUID = strawberry.field(description="UUID of the user to update.")
    input: UpdateUserV2InputGQL = strawberry.field(description="Fields to update for this user.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk updating multiple users. Each user has individual update specifications.",
        added_version="26.3.0",
    ),
    name="BulkUpdateUserV2Input",
)
class BulkUpdateUserV2InputGQL(PydanticInputMixin[BulkUpdateUsersInputDTO]):
    """Input for bulk updating users with individual specs."""

    users: list[BulkUpdateUserV2ItemInputGQL] = strawberry.field(
        description="List of user update inputs."
    )


# Delete User Inputs


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for soft-deleting multiple users. Soft delete changes user status to DELETED but preserves data.",
        added_version="26.2.0",
    ),
    name="DeleteUsersV2Input",
)
class DeleteUsersInputGQL(PydanticInputMixin[DeleteUsersInputDTO]):
    """Input for soft-deleting multiple users."""

    user_ids: list[UUID] = strawberry.field(description="List of user UUIDs to soft-delete.")


# Purge User Inputs


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for permanently deleting a user and all associated data. This action is irreversible.",
        added_version="26.2.0",
    ),
    name="PurgeUserV2Input",
)
class PurgeUserInputGQL(PydanticInputMixin[PurgeUserV2InputDTO]):
    """Input for permanently deleting a single user."""

    user_id: UUID = strawberry.field(description="UUID of the user to purge.")


@gql_pydantic_input(
    BackendAIGQLMeta(description="Options for bulk user purge operation.", added_version="26.3.0"),
    name="BulkPurgeUsersV2Options",
)
class BulkPurgeUsersV2OptionsGQL(PydanticInputMixin[BulkPurgeUsersOptionsDTO]):
    """Options for bulk user purge operation."""

    purge_shared_vfolders: bool = strawberry.field(
        default=False,
        description="If true, migrate shared virtual folders to the admin user before purging.",
    )
    delegate_endpoint_ownership: bool = strawberry.field(
        default=False,
        description="If true, delegate endpoint ownership to the admin user before purging.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for permanently deleting multiple users. This action is irreversible.",
        added_version="26.3.0",
    ),
    name="BulkPurgeUsersV2Input",
)
class BulkPurgeUsersV2InputGQL(PydanticInputMixin[BulkPurgeUsersInputDTO]):
    """Input for bulk permanently deleting multiple users."""

    user_ids: list[UUID] = strawberry.field(description="List of user UUIDs to purge.")
    options: BulkPurgeUsersV2OptionsGQL | None = strawberry.field(
        default=None,
        description="Options for the purge operation.",
    )


# IP Allowlist Inputs


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating the current user's allowed client IP list. Set allowed_client_ip to null to remove all restrictions. Use force=true to bypass the lockout safety check.",
        added_version="26.4.0",
    ),
    name="UpdateMyAllowedClientIPInput",
)
class UpdateMyAllowedClientIPInputGQL(PydanticInputMixin[UpdateMyAllowedClientIPInputDTO]):
    """Input for updating the current user's allowed client IP addresses."""

    allowed_client_ip: list[str] | None = strawberry.field(
        description=(
            "New allowed client IP addresses or CIDR ranges. "
            "Set to null to remove all IP restrictions."
        ),
    )
    force: bool = strawberry.field(
        default=False,
        description=(
            "If false (default), the operation will fail if the current request IP "
            "is not included in the new allowlist. Set to true to override this safety check."
        ),
    )
