"""User GraphQL input types for mutations."""

from __future__ import annotations

from uuid import UUID

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
    PurgeUserV2Options as PurgeUserV2OptionsDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    UpdateMyAllowedClientIPInput as UpdateMyAllowedClientIPInputDTO,
)
from ai.backend.common.dto.manager.v2.user.request import (
    UpdateUserInput as UpdateUserInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
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

    email: str = gql_field(description="User's email address. Must be unique across the system.")
    username: str = gql_field(description="Unique username for login.")
    password: str = gql_field(description="Initial password for the user.")
    domain_name: str = gql_field(description="Domain to assign the user to.")
    need_password_change: bool = gql_field(
        description="If true, user must change password on first login."
    )
    status: UserStatusEnumGQL = gql_field(description="Initial account status.")
    role: UserRoleEnumGQL = gql_field(description="User role determining access permissions.")
    full_name: str | None = gql_field(description="User's full display name.", default=None)
    description: str | None = gql_field(
        description="Optional description or notes about the user.", default=None
    )
    group_ids: list[UUID] | None = gql_field(
        description="List of project (group) IDs to assign the user to.", default=None
    )
    allowed_client_ip: list[str] | None = gql_field(
        description="Allowed client IP addresses or CIDR ranges.", default=None
    )
    totp_activated: bool = gql_field(
        description="Whether to enable TOTP two-factor authentication.", default=False
    )
    resource_policy: str = gql_field(
        description="Name of the user resource policy to apply.", default="default"
    )
    sudo_session_enabled: bool = gql_field(
        description="Whether this user can create sudo sessions.", default=False
    )
    container_uid: int | None = gql_field(
        description="User ID (UID) for container processes.", default=None
    )
    container_main_gid: int | None = gql_field(
        description="Primary group ID (GID) for container processes.", default=None
    )
    container_gids: list[int] | None = gql_field(
        description="Supplementary group IDs for container processes.", default=None
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

    users: list[CreateUserInputGQL] = gql_field(description="List of user creation inputs.")


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

    username: str | None = gql_field(description="New username.", default=UNSET)
    password: str | None = gql_field(description="New password.", default=UNSET)
    full_name: str | None = gql_field(description="New full display name.", default=UNSET)
    description: str | None = gql_field(description="New description.", default=UNSET)
    status: UserStatusEnumGQL | None = gql_field(description="New account status.", default=UNSET)
    role: UserRoleEnumGQL | None = gql_field(description="New user role.", default=UNSET)
    domain_name: str | None = gql_field(description="New domain assignment.", default=UNSET)
    group_ids: list[UUID] | None = gql_field(
        description="New project (group) assignments. Replaces existing assignments.", default=UNSET
    )
    allowed_client_ip: list[str] | None = gql_field(
        description="New allowed client IP addresses or CIDR ranges.", default=UNSET
    )
    need_password_change: bool | None = gql_field(
        description="Set password change requirement.", default=UNSET
    )
    resource_policy: str | None = gql_field(
        description="New user resource policy name.", default=UNSET
    )
    sudo_session_enabled: bool | None = gql_field(
        description="Enable or disable sudo session capability.", default=UNSET
    )
    main_access_key: str | None = gql_field(
        description="Set the primary API access key.", default=UNSET
    )
    container_uid: int | None = gql_field(description="New container user ID.", default=UNSET)
    container_main_gid: int | None = gql_field(
        description="New container primary group ID.", default=UNSET
    )
    container_gids: list[int] | None = gql_field(
        description="New container supplementary group IDs.", default=UNSET
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

    user_id: UUID = gql_field(description="UUID of the user to update.")
    input: UpdateUserV2InputGQL = gql_field(description="Fields to update for this user.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for bulk updating multiple users. Each user has individual update specifications.",
        added_version="26.3.0",
    ),
    name="BulkUpdateUserV2Input",
)
class BulkUpdateUserV2InputGQL(PydanticInputMixin[BulkUpdateUsersInputDTO]):
    """Input for bulk updating users with individual specs."""

    users: list[BulkUpdateUserV2ItemInputGQL] = gql_field(description="List of user update inputs.")


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

    user_ids: list[UUID] = gql_field(description="List of user UUIDs to soft-delete.")


# Purge User Inputs


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Options for single user purge operation.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="PurgeUserV2Options",
)
class PurgeUserV2OptionsGQL(PydanticInputMixin[PurgeUserV2OptionsDTO]):
    """Options for single user purge operation."""

    purge_shared_vfolders: bool = gql_field(
        description="If true, migrate shared virtual folders to the admin user before purging.",
        default=False,
    )
    delegate_endpoint_ownership: bool = gql_field(
        description="If true, delegate endpoint ownership to the admin user before purging.",
        default=False,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for permanently deleting a user and all associated data. This action is irreversible.",
        added_version="26.2.0",
    ),
    name="PurgeUserV2Input",
)
class PurgeUserInputGQL(PydanticInputMixin[PurgeUserV2InputDTO]):
    """Input for permanently deleting a single user."""

    user_id: UUID = gql_field(description="UUID of the user to purge.")
    options: PurgeUserV2OptionsGQL | None = gql_added_field(
        BackendAIGQLMeta(
            description="Options for the purge operation.",
            added_version=NEXT_RELEASE_VERSION,
        ),
        default=None,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Options for bulk user purge operation.", added_version="26.3.0"),
    name="BulkPurgeUsersV2Options",
)
class BulkPurgeUsersV2OptionsGQL(PydanticInputMixin[BulkPurgeUsersOptionsDTO]):
    """Options for bulk user purge operation."""

    purge_shared_vfolders: bool = gql_field(
        description="If true, migrate shared virtual folders to the admin user before purging.",
        default=False,
    )
    delegate_endpoint_ownership: bool = gql_field(
        description="If true, delegate endpoint ownership to the admin user before purging.",
        default=False,
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

    user_ids: list[UUID] = gql_field(description="List of user UUIDs to purge.")
    options: BulkPurgeUsersV2OptionsGQL | None = gql_field(
        description="Options for the purge operation.", default=None
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

    allowed_client_ip: list[str] | None = gql_field(
        description="New allowed client IP addresses or CIDR ranges. Set to null to remove all IP restrictions."
    )
    force: bool = gql_field(
        description="If false (default), the operation will fail if the current request IP is not included in the new allowlist. Set to true to override this safety check.",
        default=False,
    )
