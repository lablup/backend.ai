"""User GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

from ai.backend.common.dto.manager.v2.user.response import (
    EntityTimestamps as EntityTimestampsDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserBasicInfo as UserBasicInfoDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserContainerSettings as UserContainerSettingsDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserOrganizationInfo as UserOrganizationInfoDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserSecurityInfo as UserSecurityInfoDTO,
)
from ai.backend.common.dto.manager.v2.user.response import (
    UserStatusInfo as UserStatusInfoDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)

from .enums import UserRoleEnumGQL, UserStatusEnumGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Basic user profile information. "
            "Contains identity and descriptive fields for the user account."
        ),
    ),
    model=UserBasicInfoDTO,
    name="UserV2BasicInfo",
)
class UserBasicInfoGQL:
    """Basic user profile information."""

    username: str | None = gql_field(
        description="Unique username for login. May be null if only email-based login is used."
    )
    email: str = gql_field(description="User's email address. Used for login and notifications.")
    full_name: str | None = gql_field(description="User's full display name.")
    description: str | None = gql_field(description="Optional description or notes about the user.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "User account status information. Contains current status and password-related flags."
        ),
    ),
    model=UserStatusInfoDTO,
    name="UserV2StatusInfo",
)
class UserStatusInfoGQL:
    """User account status information."""

    status: UserStatusEnumGQL = gql_field(
        description="Current account status. See UserStatusV2 enum for possible values. Replaces the deprecated is_active field."
    )
    status_info: str | None = gql_field(
        description="Additional information about the current status, such as reason for deactivation."
    )
    need_password_change: bool | None = gql_field(
        description="If true, user must change password on next login."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "User's organizational context and permissions. "
            "Contains domain membership, role, and resource policy information."
        ),
    ),
    model=UserOrganizationInfoDTO,
    name="UserV2OrganizationInfo",
)
class UserOrganizationInfoGQL:
    """User's organizational context and permissions."""

    domain_name: str | None = gql_field(description="Name of the domain this user belongs to.")
    role: UserRoleEnumGQL | None = gql_field(
        description="User's role determining access permissions. See UserRoleV2 enum."
    )
    resource_policy: str = gql_field(
        description="Name of the user resource policy applied to this user."
    )
    main_access_key: str | None = gql_field(description="Primary API access key for this user.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "User security settings and authentication configuration. "
            "Contains IP restrictions, TOTP settings, and privilege flags."
        ),
    ),
    model=UserSecurityInfoDTO,
    name="UserV2SecurityInfo",
)
class UserSecurityInfoGQL:
    """User security settings and authentication configuration."""

    allowed_client_ip: list[str] | None = gql_field(
        description="List of allowed client IP addresses or CIDR ranges. If set, login is restricted to these IP addresses."
    )
    totp_activated: bool | None = gql_field(
        description="Whether TOTP (Time-based One-Time Password) two-factor authentication is enabled."
    )
    totp_activated_at: datetime | None = gql_field(description="Timestamp when TOTP was activated.")
    sudo_session_enabled: bool = gql_field(
        description="Whether this user can create sudo (privileged) sessions."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Container execution settings for the user. "
            "Defines UID/GID mappings for containers created by this user."
        ),
    ),
    model=UserContainerSettingsDTO,
    name="UserV2ContainerSettings",
)
class UserContainerSettingsGQL:
    """Container execution settings for the user."""

    container_uid: int | None = gql_field(
        description="User ID (UID) to use inside containers. If null, system default is used."
    )
    container_main_gid: int | None = gql_field(
        description="Primary group ID (GID) to use inside containers. If null, system default is used."
    )
    container_gids: list[int] | None = gql_field(
        description="Additional supplementary group IDs for container processes."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Common timestamp fields for entity lifecycle tracking. "
            "Reusable across different entity types."
        ),
    ),
    model=EntityTimestampsDTO,
    name="EntityTimestamps",
)
class EntityTimestampsGQL:
    """Common timestamp fields for entity lifecycle tracking."""

    created_at: datetime | None = gql_field(description="Timestamp when this entity was created.")
    modified_at: datetime | None = gql_field(
        description="Timestamp when this entity was last modified."
    )
